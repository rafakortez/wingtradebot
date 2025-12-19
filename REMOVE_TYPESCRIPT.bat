@echo off
echo ============================================================
echo Remove TypeScript Files (Deprecated)
echo ============================================================
echo.
echo TypeScript files in src/ are DEPRECATED and not used.
echo All functionality has been migrated to Python in shared/
echo.
echo This script will help you archive or remove them.
echo.
pause

echo.
echo Option 1: Archive to archive/ folder (recommended)
echo Option 2: Delete completely
echo.
set /p choice="Choose option [1/2]: "

if "%choice%"=="1" (
    echo.
    echo Creating archive...
    if not exist archive mkdir archive
    if exist archive\src_typescript_reference (
        echo Archive already exists. Removing old archive...
        rmdir /s /q archive\src_typescript_reference
    )
    xcopy /E /I /Y src archive\src_typescript_reference
    if exist package.json copy /Y package.json archive\package.json.reference
    if exist tsconfig.json copy /Y tsconfig.json archive\tsconfig.json.reference
    echo.
    echo ============================================================
    echo Archive created in archive\ folder
    echo ============================================================
    echo.
    echo TypeScript files are now archived. You can manually delete src/ if desired:
    echo   rmdir /s /q src
    echo.
) else if "%choice%"=="2" (
    echo.
    echo WARNING: This will DELETE all TypeScript files!
    echo.
    set /p confirm="Type 'yes' to confirm deletion: "
    if "%confirm%"=="yes" (
        echo.
        echo Deleting TypeScript files...
        if exist src rmdir /s /q src
        echo.
        echo ============================================================
        echo TypeScript files deleted
        echo ============================================================
    ) else (
        echo Cancelled.
    )
) else (
    echo Invalid choice. Cancelled.
)

pause

