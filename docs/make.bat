@ECHO OFF
set SPHINXBUILD=sphinx-build
set SOURCEDIR=.
set BUILDDIR=_build

if "%1" == "html" (
  %SPHINXBUILD% -W --keep-going -b html %SOURCEDIR% %BUILDDIR%\html
  exit /b %ERRORLEVEL%
)
if "%1" == "linkcheck" (
  %SPHINXBUILD% -W --keep-going -b linkcheck %SOURCEDIR% %BUILDDIR%\linkcheck
  exit /b %ERRORLEVEL%
)
ECHO Usage: make.bat [html^|linkcheck]
exit /b 1
