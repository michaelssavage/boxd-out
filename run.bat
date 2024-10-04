@echo off
echo Building the program...
go build -o main.exe

echo.
echo Testing json output:
main.exe -local -username=ottobio

echo.
echo ----------------------------------------

pause