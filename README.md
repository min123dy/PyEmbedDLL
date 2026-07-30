# PyEmbedDLL

**Python Script → Standalone DLL Builder**

PyEmbedDLL은 Python 코드를 Cython을 이용해 C 코드로 변환하고, Embedded Python Runtime 구조를 활용하여 외부 프로그램에서 호출 가능한 Windows DLL을 생성하는 빌드 도구입니다.

Python 소스 파일을 직접 배포하지 않고 Cython 기반 Native DLL 형태로 패키징할 수 있도록 설계되었습니다.

---

# 🤖 AI 사용 안내

이 프로젝트는 개발 과정에서 AI(인공지능 도구)의 도움을 받아 제작되었습니다.

AI는 다음 과정에서 활용되었습니다.

- 전체 구조 설계 보조
- Embedded Python Runtime 구현 검토
- Cython 기반 DLL 구조 설계
- Windows API 사용 검토
- 오류 분석 및 디버깅 지원
- 코드 개선 방향 제안

생성된 코드는 개발자가 직접 검토하고 수정하여 완성하였습니다.

---

# ✨ 주요 기능

## Python 파일을 DLL로 변환

Python 파일

```text
example.py
```

를 Cython을 이용하여 DLL로 변환합니다.

```text
Python Source
      │
      ▼
   Cython
      │
      ▼
 Generated C
      │
      ▼
    MSVC
      │
      ▼
 Windows DLL
```

생성된 DLL은 Python 소스 파일을 함께 배포할 필요가 없습니다.

---

# 🔥 특징

## Cython 기반 Native 변환

PyEmbedDLL은 단순한 Python 패키징 방식이 아니라 Cython을 이용하여 Python 코드를 C 코드로 변환한 후 MSVC로 컴파일합니다.

```text
Python
   │
   ▼
Cython
   │
   ▼
C Source
   │
   ▼
Windows DLL
```

---

## Embedded Python Runtime

빌드 시 Python 실행에 필요한 파일들을 DLL 내부 Resource로 포함합니다.

포함 가능한 항목

- Python DLL
- Python Extension Module (.pyd)
- Python Standard Library (Lib)
- 기타 Python Runtime 의존 파일

DLL 실행 시 필요한 파일을 임시 디렉터리로 자동 추출하여 Python 실행 환경을 구성합니다.

---

## Python Runtime 자동 초기화

DLL은 최초 호출 시 자동으로

- Embedded Resource 추출
- Python Runtime 초기화
- sys.path 구성
- Embedded Module 등록

을 수행합니다.

사용자가 별도로 Python을 초기화할 필요가 없습니다.

---

## start() / main() 자동 실행

DLL에서 Export되는 함수

```c
start()
```

를 호출하면 Python 모듈에서

```python
def start():
    ...
```

를 우선 실행합니다.

start()가 존재하지 않는 경우

```python
def main():
    ...
```

을 자동으로 호출합니다.

---

## 사용자 지정 Python 경로

빌드 시 사용할 Python Runtime을 지정할 수 있습니다.

예시

```text
python build_single_file_dll.py example.py plugin.dll -p "C:\Python312"
```

또는

```text
python build_single_file_dll.py example.py plugin.dll --python-home "C:\Python312"
```

지정하지 않으면 현재 실행 중인 Python 환경을 사용합니다.

---

# ⚠️ 지원 환경

## 운영체제

현재 지원

- Windows

---

## Python

현재 테스트 완료

```text
Python 3.12.x
```

Python C Extension은 ABI에 종속됩니다.

예시

```text
Build
Python 3.12

↓

Runtime
Python 3.14
```

지원되지 않습니다.

다른 Python 버전을 사용하려면 해당 버전에서 다시 빌드해야 합니다.

---

# 📦 요구 사항

## Python

Python 3.12

확인

```text
python --version
```

---

## Python Package

Cython 설치

```text
pip install cython
```

---

## Microsoft Build Tools

필수 구성 요소

- MSVC Compiler (cl.exe)
- Windows SDK
- Resource Compiler (rc.exe)

Visual Studio Installer에서

```text
Desktop development with C++
```

워크로드를 설치해야 합니다.

---

# 🛠️ 빌드 방법

Python 파일 준비

```text
example.py
```

예시

```python
def start():
    print("Hello from PyEmbedDLL!")
```

빌드

```text
python build_single_file_dll.py example.py plugin.dll
```

또는

```text
python build_single_file_dll.py example.py plugin.dll -p "C:\Python312"
```

빌드 완료

```text
plugin.dll
```

생성됩니다.

---

# 🚀 사용 방법

생성된 DLL은 C#, C/C++ 등 DLL을 호출할 수 있는 환경에서 사용할 수 있습니다.

## C# 예제

```csharp
using System;
using System.Runtime.InteropServices;

class Program
{
    [DllImport("plugin.dll")]
    static extern void start();

    static void Main()
    {
        start();
    }
}
```

---

# ⚙️ 동작 구조

```text
Python Source
      │
      ▼
   Cython
      │
      ▼
 Generated C
      │
      ▼
    MSVC
      │
      ▼
 Windows DLL
      │
      ├── Embedded Python Runtime
      ├── Embedded Standard Library
      ├── Embedded Extension Modules
      ├── Embedded Resources
      │
      ▼
Extract to Temporary Directory
      │
      ▼
Python Runtime Initialization
      │
      ▼
start() / main()
```

---

# ⚠️ 제한 사항

- 현재 Windows만 지원합니다.
- Python 3.12 기준으로 제작되었습니다.
- Python 버전이 변경되면 다시 빌드해야 합니다.
- 실행 시 Embedded Resource를 임시 디렉터리로 추출합니다.
- 완전한 메모리 전용 실행(In-Memory Execution)은 현재 지원하지 않습니다.
- Cython이 지원하지 않는 일부 Python 기능은 제한될 수 있습니다.

---

# 📜 License

This project is licensed under the **Mozilla Public License Version 2.0 (MPL-2.0).**

You may use, modify, and distribute this software under the terms of the MPL-2.0.

For the full license text, see:

https://mozilla.org/MPL/2.0/

---

본 프로젝트는 **Mozilla Public License Version 2.0 (MPL-2.0)**에 따라 배포됩니다.

사용, 수정 및 배포는 MPL-2.0의 조건을 따라야 합니다.

본 소프트웨어의 사용으로 인해 발생하는 문제나 손해에 대한 책임은 사용자에게 있습니다.
