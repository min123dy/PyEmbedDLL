# PyEmbedDLL

**Python Script → Standalone DLL Builder**

PyDLLForge는 Python 코드를 Cython을 이용해 C 코드로 변환하고, Embedded Python Runtime 구조를 활용하여 외부 프로그램에서 호출 가능한 DLL을 생성하는 빌드 도구입니다.

Python 소스 파일을 직접 배포하지 않고 Cython 기반 Native DLL 형태로 패키징할 수 있도록 설계되었습니다.

---

## 🤖 AI 사용 안내

이 프로젝트는 개발 과정에서 AI(인공지능 도구)의 도움을 받아 제작되었습니다.

AI는 다음 과정에서 활용되었습니다.

- 전체 구조 설계 보조
- C/C++ 및 Python Embedded 관련 구현 검토
- 오류 분석 및 디버깅 지원
- 코드 개선 방향 제안

생성된 코드는 개발자가 직접 검토하고 수정하여 완성하였습니다.

---

# ✨ 주요 기능

## Python 파일을 DLL로 변환

Python 파일:

```
example.py
```

를 Cython을 이용해 변환합니다.

```
.py
 |
 v
Cython
 |
 v
C Code
 |
 v
MSVC
 |
 v
DLL
```

생성된 DLL은 원본 Python 파일 없이 실행 가능합니다.

---

# 🔥 특징

## Cython 기반 Native 변환

PyDLLForge는 단순 Python 패키징 방식이 아니라 Cython 기반 변환 방식을 사용합니다.

변환 과정:

```
Python Source
      |
      v
   Cython
      |
      v
 Generated C Code
      |
      v
 Windows DLL
```

---

## Embedded Python Runtime

빌드 과정에서 필요한 Python 구성 요소를 DLL 내부 리소스로 포함할 수 있습니다.

포함 대상:

- Python 표준 라이브러리
- Python 확장 모듈 (.pyd)
- Python DLL
- 기타 의존 파일

실행 시 필요한 환경을 구성하여 내장된 Python 코드를 실행합니다.

---

# ⚠️ 지원 환경

## Python Version

현재 지원 및 테스트 버전:

```
Python 3.12.x
```

Python C Extension은 ABI 버전에 영향을 받습니다.

예:

```
Build:
Python 3.12

Runtime:
Python 3.14

지원하지 않음
```

다른 Python 버전을 사용하려면 해당 버전 환경에서 다시 빌드해야 합니다.

---

# 📦 요구 사항

## Python

Python 3.12 필요

확인:

```
python --version
```

---

## Python Package

Cython 설치:

```
pip install cython
```

---

## Microsoft Build Tools

필요:

- MSVC Compiler
- Windows SDK
- Resource Compiler (rc.exe)

Visual Studio 설치 시:

```
Desktop development with C++
```

워크로드 필요

---

# 🛠️ 빌드 방법

Python 파일 준비:

```
example.py
```

예:

```python
def start():
    print("Hello from PyDLLForge!")
```

---

빌더 실행:

```
python builder.py example.py
```

DLL 이름 입력:

```
plugin.dll
```

결과:

```
plugin.dll
```

생성

---

# 🚀 사용 방법

생성된 DLL은 C#, C/C++ 등 DLL 호출이 가능한 환경에서 사용할 수 있습니다.

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

```
Python Source
      |
      v
   Cython
      |
      v
 Generated C
      |
      v
    MSVC
      |
      v
 Windows DLL
      |
      +-- Cython Module
      |
      +-- Python Runtime
      |
      +-- Embedded Resources
```

---

# ⚠️ 제한 사항

- 현재 Python 3.12 기준으로 제작되었습니다.
- Python 버전이 다르면 다시 빌드해야 합니다.
- 현재 방식은 실행 시 필요한 파일을 임시 위치에 추출합니다.
- 완전한 메모리 전용 실행 방식은 아닙니다.

---

# 📜 License

This project is licensed under the Mozilla Public License Version 2.0 (MPL-2.0).

You may use, modify, and distribute this software under the terms of the MPL-2.0.

See the full license text:

```
Mozilla Public License Version 2.0
```

For more information, visit:

https://mozilla.org/MPL/2.0/

---

본 프로젝트는 Mozilla Public License 2.0 (MPL-2.0)에 따라 배포됩니다.

소프트웨어의 사용, 수정 및 배포는 MPL-2.0의 조건을 따라야 합니다.

사용으로 인해 발생하는 문제에 대한 책임은 사용자에게 있습니다.
