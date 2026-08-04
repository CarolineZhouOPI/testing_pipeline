@echo off
setlocal
REM Clean previous results
if exist allure_results rmdir /s /q allure_results
if exist allure_report rmdir /s /q allure_report
mkdir allure_results

REM Run tests without explicit sequential/parallel markers
set GENERATE_ALLURE_REPORT=1
set "_OLD_JAVA_HOME=%JAVA_HOME%"
set "JAVA_HOME="
py -m pytest -m "not sequential and not parallel" -v -s --alluredir=allure_results --junitxml=results.xml
set GENERATE_ALLURE_REPORT=
set "JAVA_HOME=%_OLD_JAVA_HOME%"
set "_OLD_JAVA_HOME="
endlocal

REM (Optional) Generate Allure report if Allure is installed
REM allure generate allure_results -o allure_report --clean
