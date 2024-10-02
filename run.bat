@echo off
echo Building the program...
go build -o boxd.exe

echo.
echo Testing json output:
boxd.exe -local -username=ottobio

echo.
echo ----------------------------------------

pause