/*
MIT License

Copyright (c) 2018 Ryan L. Guy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/


#ifndef FLUIDENGINE_LOGFILE_H
#define FLUIDENGINE_LOGFILE_H

#include <string>
#include <vector>
#include <sstream>

#include "threadutils.h"

class LogFile
{
public:
    LogFile();
    ~LogFile();

    LogFile(LogFile &obj) {
        _startTimeString = obj._startTimeString;
        _separator = obj._separator;
    }

    LogFile operator=(LogFile &rhs)
    {
        _startTimeString = rhs._startTimeString;
        _separator = rhs._separator;
        
        return *this;
    }

    void setSeparator(std::string separator);
    void enableConsole();
    void disableConsole();
    bool isConsoleEnabled();
    std::string getString();
    void clear();
    void newline();
    void separator();
    void timestamp();
    void logString(const std::string& str);
    void log(std::ostream &out);
    void log(std::string str, int indentLevel = 0);
    void log(std::string str, int value, int indentLevel = 0);
    void log(std::string str, double value, int precision = 0, int indentLevel = 0);
    void log(std::string str, std::string value = "", int indentLevel = 0);
    std::string getTime();
    void print(std::string str);
    std::vector<char> flush();

private:
    void _print(std::string str);

    std::string _startTimeString;
    std::string _separator;
    std::ostringstream _stream;
    bool _isWritingToConsole = true;

    std::mutex _mutex;
};

#endif