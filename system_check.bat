@echo off
echo Simple System Check for Python, PyTorch, CUDA, and GPU
echo ====================================================

:: Add CUDA path (matched to your toolkit version)
set "PATH=%PATH%;C:\Windows\System32;C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin"

:: Check Python
echo Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install from https://www.python.org/downloads/
) else (
    python --version
)
echo.

:: Check PyTorch
echo Checking PyTorch...
python -c "import torch; print('PyTorch Version: ' + torch.__version__)" 2>nul || echo ERROR: PyTorch not installed. Install from https://pytorch.org/get-started/locally/
echo.

:: Check GPU and driver
echo Checking GPU and Driver...
where nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: nvidia-smi not found. Check NVIDIA drivers at https://www.nvidia.com/Download/index.aspx
) else (
    nvidia-smi
)
echo.

:: Check CUDA Toolkit
echo Checking CUDA Toolkit...
where nvcc >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: CUDA Toolkit not installed. Get it from https://developer.nvidia.com/cuda-downloads
) else (
    nvcc --version
)
echo.

:: Check PyTorch CUDA and GPU compatibility with functional test
echo Checking PyTorch CUDA and GPU Compatibility...
:: Create temp_check.py with proper escaping
echo import sys > temp_check.py
echo try: >> temp_check.py
echo     import torch >> temp_check.py
echo     print('CUDA Available: ' + ('Yes' if torch.cuda.is_available() else 'No')) >> temp_check.py
echo     print('PyTorch CUDA Version: ' + (torch.version.cuda if torch.version.cuda else 'None')) >> temp_check.py
echo     print('GPU Compute Capability: ' + (str(torch.cuda.get_device_capability()) if torch.cuda.is_available() else 'No GPU')) >> temp_check.py
echo     supported = [50, 60, 61, 70, 75, 80, 86, 89, 90, 120] >> temp_check.py
echo     cc = torch.cuda.get_device_capability() if torch.cuda.is_available() else (0, 0) >> temp_check.py
echo     cc_val = cc[0] * 10 + cc[1] >> temp_check.py
echo     static_compat = 'OK' if cc_val in supported else 'Not in static list (may still work in nightly builds)' >> temp_check.py
echo     print('Static GPU Compatibility: ' + static_compat) >> temp_check.py
echo     try: >> temp_check.py
echo         x = torch.rand(5, 3).cuda() >> temp_check.py
echo         print('Functional GPU Test: OK (tensor created on GPU: ' + str(x.device) + ')') >> temp_check.py
echo     except Exception as e: >> temp_check.py
echo         print('Functional GPU Test: Failed - ' + str(e)) >> temp_check.py
echo     print('Note: Basic support OK since PyTorch 2.7+; check advanced features if issues arise.') >> temp_check.py
echo except ImportError: >> temp_check.py
echo     print('ERROR: PyTorch not installed. Install from https://pytorch.org/get-started/locally/') >> temp_check.py
echo except Exception as e: >> temp_check.py
echo     print('ERROR: CUDA check failed - ' + str(e)) >> temp_check.py
:: Verify file creation
if not exist temp_check.py (
    echo ERROR: Failed to create temp_check.py. Check write permissions in D:\karaoke_app.
    goto :cleanup
)
:: Run the Python script
python temp_check.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to run temp_check.py. Check Python environment or script syntax.
)
:: Cleanup
:cleanup
if exist temp_check.py (
    del temp_check.py
)
echo.

echo ====================================================
echo Check complete. Review any errors above. The functional test confirms real-world compatibility - trust that over static checks.
pause