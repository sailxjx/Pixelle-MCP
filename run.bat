@echo off
setlocal enabledelayedexpansion

REM Script directory
set "SCRIPT_DIR=%~dp0"
set "PID_FILE=%SCRIPT_DIR%.pids"
set "LOG_DIR=%SCRIPT_DIR%logs"

REM Create log directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Color output functions (Windows doesn't support colors easily, so we'll use text)
:print_info
echo [INFO] %~1
goto :eof

:print_success
echo [SUCCESS] %~1
goto :eof

:print_error
echo [ERROR] %~1
goto :eof

:print_warning
echo [WARNING] %~1
goto :eof

REM Check if uv is installed
:check_uv
uv --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Please install uv first"
    echo Installation: curl -LsSf https://astral.sh/uv/install.sh ^| sh
    exit /b 1
)
goto :eof

REM Stop existing services
:stop_services
if exist "%PID_FILE%" (
    call :print_info "Stopping existing services..."
    for /f "tokens=*" %%i in (%PID_FILE%) do (
        if not "%%i"=="" (
            taskkill /PID %%i /F >nul 2>&1
            call :print_info "Stopped process %%i"
        )
    )
    del "%PID_FILE%" >nul 2>&1
    call :print_success "All services stopped"
) else (
    call :print_info "No running services found"
)
goto :eof

REM Check if port is occupied
:check_port
set "port=%~1"
netstat -an | find ":%port% " | find "LISTENING" >nul
if not errorlevel 1 (
    call :print_warning "Port %port% is occupied, attempting to release..."
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":%port% " ^| find "LISTENING"') do (
        taskkill /PID %%a /F >nul 2>&1
        call :print_info "Released port %port% (PID: %%a)"
    )
)
goto :eof

REM Start single service
:start_service
set "service_name=%~1"
set "service_dir=%~2"
set "port=%~3"

call :print_info "Starting %service_name%..."
cd /d "%SCRIPT_DIR%%service_dir%"

REM Sync dependencies
uv sync

REM Check and release port
call :check_port "%port%"

REM Start service in foreground
start "Pixelle MCP - %service_name%" cmd /c "uv run main.py"
set "pid=!errorlevel!"

cd /d "%SCRIPT_DIR%"

REM Wait for service to start
timeout /t 3 /nobreak >nul
call :print_success "%service_name% started"
goto :eof

REM Start all services
:start_services
call :print_info "Starting Pixelle MCP services..."

REM Clear PID file
echo. > "%PID_FILE%" 2>nul

REM Start base service
call :start_service "mcp-base" "mcp-base" "9001"

REM Start server service  
call :start_service "mcp-server" "mcp-server" "9002"

REM Start client service
call :start_service "mcp-client" "mcp-client" "9003"

call :print_success "All services started successfully!"
echo 🌐 Client: http://localhost:9003
echo 🗄️ Server: http://localhost:9002  
echo 🔧 Base Service: http://localhost:9001
echo.
echo Press Ctrl+C to stop all services
goto :eof

REM Check service status
:show_status
call :print_info "Checking service status..."

if not exist "%PID_FILE%" (
    call :print_info "No running services"
    goto :eof
)

set "running_count=0"
set "services=mcp-base:9001 mcp-server:9002 mcp-client:9003"

for %%s in (%services%) do (
    for /f "tokens=1,2 delims=:" %%a in ("%%s") do (
        set "service_name=%%a"
        set "port=%%b"
        netstat -an | find ":%port% " | find "LISTENING" >nul
        if not errorlevel 1 (
            call :print_success "!service_name! is running (Port: !port!)"
            set /a running_count+=1
        ) else (
            call :print_error "!service_name! is not running"
        )
    )
)

echo Running services: %running_count%/3
goto :eof

REM Show help information
:show_help
echo Usage: %~nx0 [command]
echo.
echo Commands:
echo   start            Start all services (foreground)
echo   stop             Stop all services
echo   restart          Restart all services
echo   status           Check service status
echo   help             Show help information
echo.
echo Examples:
echo   %~nx0 start      # Start services
echo   %~nx0 restart    # Restart all services
goto :eof

REM Main logic
:main
set "command=%~1"

REM Default to start if no command specified
if "%command%"=="" set "command=start"

if "%command%"=="start" (
    call :check_uv
    call :stop_services
    call :start_services
    echo.
    echo Services are running. Press any key to stop all services...
    pause >nul
    call :stop_services
) else if "%command%"=="stop" (
    call :stop_services
) else if "%command%"=="restart" (
    call :check_uv
    call :stop_services
    call :start_services
) else if "%command%"=="status" (
    call :show_status
) else if "%command%"=="help" (
    call :show_help
) else (
    call :print_error "Unknown command: %command%"
    call :show_help
    exit /b 1
)

goto :eof

REM Run main function
call :main %* 