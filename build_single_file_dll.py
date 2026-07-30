# Copyright (c) 2026 min123dy
#
# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
import shutil
import subprocess
import tempfile
import argparse
from pathlib import Path

# 빌더 스크립트 실행 중 __pycache__ 폴더 생성 방지
sys.dont_write_bytecode = True

def build_single_file_dll(
    target_py_path: str,
    output_dll_name: str = "output.dll",
    python_path: str = None
):
    target_path = Path(target_py_path).resolve()
    if not target_path.exists():
        print(f"오류: 지정한 파일 '{target_py_path}'을 찾을 수 없습니다.")
        return False

    script_dir = target_path.parent
    module_name = target_path.stem

    # Python 경로 결정
    if python_path:
        py_base = Path(python_path).resolve()
        if py_base.is_file():
            py_base = py_base.parent
        print(f"[Builder] 사용자 지정 Python 사용: {py_base}")
    else:
        py_base = Path(sys.base_prefix)
        print(f"[Builder] 기본 Python 사용: {py_base}")

    if not py_base.exists():
        print(f"오류: 지정한 Python 경로 '{py_base}'가 존재하지 않습니다.")
        return False

    # 임시 작업 공간 생성
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"[1/6] 임시 빌드 디렉터리 준비: {temp_path}")

        # 1. 원본 .py 복사
        target_py_in_temp = temp_path / f"{module_name}.py"
        shutil.copy(target_path, target_py_in_temp)

        # 2. Cython 실행 (.py -> .c)
        print(f"[2/6] Cython 변환 진행 중 ({module_name}.py -> {module_name}.c)...")
        cython_env = os.environ.copy()
        cython_env["PYTHONDONTWRITEBYTECODE"] = "1"

        try:
            subprocess.run(
                [sys.executable, "-B", "-m", "cython", "-3", f"{module_name}.py"],
                cwd=temp_path,
                env=cython_env,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Cython 변환 실패:\n{e.stderr}")
            return False

        # 3. 내장할 의존 파일 (.pyd, .dll, Lib 전체) 수집 및 .rc 파일 생성
        print("[3/6] 의존 파일 및 표준 라이브러리(Lib) 수집 중...")
        target_files = [] # (절대 경로, 상대 저장 경로)

        # 3-1. DLLs 디렉터리의 C-의존성 DLL, PYD 및 파이썬 핵심 DLL 수집
        dlls_dir = py_base / "DLLs"
        if dlls_dir.exists():
            for f in dlls_dir.glob("*"):
                if f.suffix.lower() in ('.pyd', '.dll'):
                    target_files.append((f, f.name))

        # Python 루트 디렉터리의 python3*.dll 수집
        for f in py_base.glob("python3*.dll"):
            target_files.append((f, f.name))

        # 3-2. 파이썬 표준 라이브러리(Lib) 전체 수집 (Lib/... 경로 유지)
        lib_dir = py_base / "Lib"
        if lib_dir.exists():
            for root, dirs, files in os.walk(lib_dir):
                dirs[:] = [d for d in dirs if d not in ('__pycache__', 'test', 'tests', 'idlelib', 'tkinter', 'turtledemo')]
                for file in files:
                    if file.endswith(('.pyc', '.pyo')):
                        continue
                    full_p = Path(root) / file
                    rel_p = full_p.relative_to(py_base)
                    target_files.append((full_p, str(rel_p)))

        seen_names = set()
        resource_entries = []
        res_id = 101

        rc_content = "#include <windows.h>\n\n"

        for full_path, rel_path in target_files:
            if full_path.name.lower() == output_dll_name.lower():
                continue
            if rel_path in seen_names:
                continue
            seen_names.add(rel_path)

            escaped_path = str(full_path).replace("\\", "\\\\")
            rc_content += f"{res_id} RCDATA \"{escaped_path}\"\n"
            resource_entries.append((res_id, rel_path.replace("\\", "/")))
            res_id += 1

        rc_file = temp_path / "resources.rc"
        rc_file.write_text(rc_content, encoding="utf-8")

        # 4. Windows Resource Compiler (rc.exe) 실행
        print("[4/6] Resource Compiler(rc.exe) 컴파일 중...")
        res_file = temp_path / "resources.res"
        try:
            subprocess.run(
                ["rc", "/fo", str(res_file), str(rc_file)],
                cwd=temp_path,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"rc.exe 실행 실패:\n{e.stderr}")
            return False

        # 5. C 파일 생성
        python_home = str(py_base).replace('\\', '/')
        
        c_res_array_items = []
        for r_id, r_name in resource_entries:
            c_res_array_items.append(f'    {{ {r_id}, "{r_name}" }}')
        c_res_array_items.append('    { 0, NULL }')
        c_res_array_str = ",\n".join(c_res_array_items)

        c_template = r"""#include <windows.h>
#include <stdio.h>
#include <Python.h>

#define DllExport __declspec(dllexport)

HMODULE g_hModule = NULL;
char g_tempExtractDir[MAX_PATH] = {0};

PyMODINIT_FUNC PyInit___MODULE_NAME__(void);

struct ResourceEntry {
    int id;
    const char* name;
};

struct ResourceEntry g_Resources[] = {
__RESOURCE_ARRAY__
};

void CreateDirectoriesRecursive(const char* path) {
    char temp[MAX_PATH];
    char* p = NULL;
    size_t len;

    snprintf(temp, sizeof(temp), "%s", path);
    len = strlen(temp);
    if (temp[len - 1] == '/' || temp[len - 1] == '\\') {
        temp[len - 1] = 0;
    }

    for (p = temp + 1; *p; p++) {
        if (*p == '/' || *p == '\\') {
            *p = 0;
            CreateDirectoryA(temp, NULL);
            *p = '/';
        }
    }
    CreateDirectoryA(temp, NULL);
}

void ExtractEmbeddedResources() {
    char tempPath[MAX_PATH];
    GetTempPathA(MAX_PATH, tempPath);
    
    DWORD pid = GetCurrentProcessId();
    sprintf_s(g_tempExtractDir, MAX_PATH, "%spy_dll_embed_%lu", tempPath, pid);
    CreateDirectoryA(g_tempExtractDir, NULL);

    SetDllDirectoryA(g_tempExtractDir);

    for (int i = 0; g_Resources[i].id != 0; i++) {
        HRSRC hRes = FindResourceA(g_hModule, MAKEINTRESOURCEA(g_Resources[i].id), RT_RCDATA);
        if (!hRes) continue;

        HGLOBAL hData = LoadResource(g_hModule, hRes);
        if (!hData) continue;

        DWORD dwSize = SizeofResource(g_hModule, hRes);
        LPVOID pData = LockResource(hData);

        char outFile[MAX_PATH];
        sprintf_s(outFile, MAX_PATH, "%s/%s", g_tempExtractDir, g_Resources[i].name);

        char dirPath[MAX_PATH];
        sprintf_s(dirPath, MAX_PATH, "%s", outFile);
        char* lastSlash = strrchr(dirPath, '/');
        if (lastSlash != NULL) {
            *lastSlash = '\0';
            CreateDirectoriesRecursive(dirPath);
        }

        HANDLE hFile = CreateFileA(outFile, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
        if (hFile != INVALID_HANDLE_VALUE) {
            DWORD dwWritten = 0;
            WriteFile(hFile, pData, dwSize, &dwWritten, NULL);
            CloseHandle(hFile);
        }
    }
}

void InitPython() {
    if (!Py_IsInitialized()) {
        ExtractEmbeddedResources();

        if (PyImport_AppendInittab("__MODULE_NAME__", PyInit___MODULE_NAME__) == -1) {
            PySys_WriteStderr("오류: PyImport_AppendInittab 실패!\n");
            return;
        }

        Py_SetPythonHome(L"__PYTHON_HOME__");
        Py_DontWriteBytecodeFlag = 1;
        Py_IgnoreEnvironmentFlag = 1;

        Py_Initialize();

        PyObject *sys_path = PySys_GetObject("path");
        if (sys_path != NULL) {
            PyObject *pPathObj = PyUnicode_FromString(g_tempExtractDir);
            PyList_Insert(sys_path, 0, pPathObj);
            Py_DECREF(pPathObj);

            char libPath[MAX_PATH];
            sprintf_s(libPath, MAX_PATH, "%s/Lib", g_tempExtractDir);
            PyObject *pLibObj = PyUnicode_FromString(libPath);
            PyList_Insert(sys_path, 1, pLibObj);
            Py_DECREF(pLibObj);
        }

        PyEval_SaveThread();
    }
}

DllExport void start() {
    InitPython();

    PyGILState_STATE gstate = PyGILState_Ensure();

    PyObject *sys_modules = PyImport_GetModuleDict();
    PyObject *pModule = PyDict_GetItemString(sys_modules, "__MODULE_NAME__");

    if (pModule == NULL) {
        PyObject *pRawObj = PyInit___MODULE_NAME__();

        if (pRawObj != NULL) {
            if (PyModule_Check(pRawObj)) {
                pModule = pRawObj;
                Py_INCREF(pModule);
            } else {
                PyModuleDef *pDef = (PyModuleDef*)pRawObj;
                
                PyObject *pImportLib = PyImport_ImportModule("importlib.machinery");
                if (pImportLib != NULL) {
                    PyObject *pSpecClass = PyObject_GetAttrString(pImportLib, "ModuleSpec");
                    if (pSpecClass != NULL) {
                        PyObject *pName = PyUnicode_FromString("__MODULE_NAME__");
                        PyObject *pArgs = PyTuple_Pack(2, pName, Py_None);
                        
                        PyObject *pSpec = PyObject_CallObject(pSpecClass, pArgs);
                        
                        if (pSpec != NULL) {
                            pModule = PyModule_FromDefAndSpec(pDef, pSpec);
                            if (pModule != NULL) {
                                if (PyModule_ExecDef(pModule, pDef) < 0) {
                                    Py_DECREF(pModule);
                                    pModule = NULL;
                                }
                            }
                            Py_DECREF(pSpec);
                        }
                        Py_DECREF(pName);
                        Py_DECREF(pArgs);
                        Py_DECREF(pSpecClass);
                    }
                    Py_DECREF(pImportLib);
                }
            }

            if (pModule != NULL) {
                PyDict_SetItemString(sys_modules, "__MODULE_NAME__", pModule);
            }
        }
    } else {
        Py_INCREF(pModule);
    }

    if (pModule != NULL) {
        PyObject *pFunc = PyObject_GetAttrString(pModule, "start");
        if (pFunc == NULL) {
            PyErr_Clear();
            pFunc = PyObject_GetAttrString(pModule, "main");
        }

        if (pFunc && PyCallable_Check(pFunc)) {
            PyObject *pResult = PyObject_CallObject(pFunc, NULL);
            if (pResult != NULL) {
                Py_DECREF(pResult);
            } else {
                PyErr_Print();
            }
            Py_DECREF(pFunc);
        } else {
            PySys_WriteStdout("[__MODULE_NAME__] start() 또는 main() 함수를 찾을 수 없습니다.\n");
        }
        Py_DECREF(pModule);
    } else {
        PySys_WriteStderr("오류: Cython 내장 모듈 Exec 초기화 실패\n");
        PyErr_Print();
    }

    PyGILState_Release(gstate);
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        g_hModule = hinstDLL;
    }
    return TRUE;
}
"""
        c_code = (
            c_template
            .replace("__MODULE_NAME__", module_name)
            .replace("__PYTHON_HOME__", python_home)
            .replace("__RESOURCE_ARRAY__", c_res_array_str)
        )

        c_file = temp_path / "dll_main.c"
        c_file.write_text(c_code, encoding="utf-8")

        # 6. MSVC 컴파일 및 링크
        print("[5/6] C 컴파일러(cl.exe) 및 리소스 통합 빌드 중...")
        py_include = py_base / "include"
        py_libs = py_base / "libs"
        
        lib_files = list(py_libs.glob("python3*.lib"))
        if not lib_files:
            print(f"오류: '{py_libs}' 경로에서 python3*.lib 파일을 찾을 수 없습니다.")
            return False
        py_lib_file = lib_files[0]

        final_dll_path = script_dir / output_dll_name

        compile_cmd = [
            "cl", "/LD", "/O2", "/utf-8",
            "dll_main.c", f"{module_name}.c", str(res_file),
            f"/I{py_include}",
            "/link",
            f"/LIBPATH:{py_libs}",
            str(py_lib_file),
            f"/OUT:{final_dll_path}"
        ]

        try:
            subprocess.run(
                compile_cmd,
                cwd=temp_path,
                check=True,
                capture_output=True,
                text=True
            )
            print(f"[6/6] 빌드 성공!")
            print(f"  └─ 생성된 DLL: {final_dll_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"C 컴파일 실패:\n{e.stdout}\n{e.stderr}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Standalone Python DLL Builder"
    )

    parser.add_argument(
        "target_file",
        nargs="?",
        help="변환할 py 파일 경로"
    )

    parser.add_argument(
        "dll_name",
        nargs="?",
        default="plugin1.dll",
        help="생성할 DLL 이름 (기본값: plugin1.dll)"
    )

    parser.add_argument(
        "-p",
        "--python",
        "--python-home",
        dest="python_path",
        default=None,
        help="DLL 내부에 하드코딩할 Python 경로 (디렉터리 또는 python.exe 경로)"
    )

    args = parser.parse_args()

    if args.target_file:
        target_file = args.target_file
    else:
        target_file = input("변환할 .py 파일 경로를 입력하세요: ").strip('"')

    dll_name = args.dll_name
    if not dll_name.endswith(".dll"):
        dll_name += ".dll"

    build_single_file_dll(
        target_file,
        dll_name,
        python_path=args.python_path
    )