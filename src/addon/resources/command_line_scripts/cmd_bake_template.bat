echo off
chcp 65001
set /a launch_attempts = MAX_LAUNCH_ATTEMPTS
set /a launch_counter = %launch_attempts%
:DoWhile
    if %launch_counter% == 0 goto EndDoWhile
    @echo on
    COMMAND_OPERATION
    @echo off
    if %errorlevel% == 0 goto EndDoWhile else (
        set /a current_restart = %launch_attempts% - %launch_counter% + 1
        set /a max_restarts = %launch_attempts% - 1
        echo --------------------------------------------------------------------------------
        echo SIMULATION TERMINATED: An unknown error has caused Blender to crash ^(error code %ERRORLEVEL%^)
        if %launch_counter% neq 1 (
            echo Attempting to re-launch simulation ^(attempt %current_restart% / %max_restarts%^)
        )
        echo --------------------------------------------------------------------------------
    )
    set /a launch_counter = %launch_counter% - 1
    if %launch_counter% gtr 0 goto DoWhile
:EndDoWhile
cmd /k