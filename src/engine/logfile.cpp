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

#include "logfile.h"

#include <cmath>
#include <time.h>
#include <iostream>

LogFile::LogFile() : _startTimeString(getTime()),
                     _separator("------------------------------------------------------------") {
}

LogFile::~LogFile() {
}

void LogFile::setSeparator(std::string sep) {
    std::unique_lock<std::mutex> lock(_mutex);
    _separator = sep;
}

void LogFile::enableConsole() {
    std::unique_lock<std::mutex> lock(_mutex);
    _isWritingToConsole = true;
}

void LogFile::disableConsole() {
    std::unique_lock<std::mutex> lock(_mutex);
    _isWritingToConsole = false;
}

bool LogFile::isConsoleEnabled() {
    return _isWritingToConsole;
}

std::string LogFile::getString() {
    return _stream.str();
}

void LogFile::clear() {
    std::unique_lock<std::mutex> lock(_mutex);
    _stream.str(std::string());
}

void LogFile::newline() {
    std::unique_lock<std::mutex> lock(_mutex);
    _stream << std::endl;
    _print("\n");
}

void LogFile::separator() {
    std::unique_lock<std::mutex> lock(_mutex);
    _stream << _separator << std::endl;
    _print(_separator + "\n");
}

void LogFile::timestamp() {
    std::string time = getTime();
    std::unique_lock<std::mutex> lock(_mutex);
    _stream << time << std::endl;
    _print(time + "\n");
}

void LogFile::logString(const std::string& str) {
    std::unique_lock<std::mutex> lock(_mutex);
    _stream << str << std::endl;
    _print(str + "\n");
}

void LogFile::log(std::ostream &s) {
    std::ostringstream &out = dynamic_cast<std::ostringstream&>(s);
    std::unique_lock<std::mutex> lock(_mutex);
    _stream << out.str();
    _print(out.str());
}

void LogFile::log(std::string str, int indentLevel) {
    log(str, "", indentLevel);
}

void LogFile::log(std::string str, int value, int indentLevel) {
    std::ostringstream v;
    v << value;
    log(str, v.str(), indentLevel);
}

void LogFile::log(std::string str, double value, int precision, int indentLevel) {
    double scale = (double)pow(10, precision);
    std::ostringstream v;
    v << floor(value*scale) / (scale);
    log(str, v.str(), indentLevel);
}

void LogFile::log(std::string str, std::string value, int indentLevel) {
    std::ostringstream out;
    for (int i = 0; i < indentLevel; i++) {
        out << "\t";
    }

    out << str << value << std::endl;
    std::unique_lock<std::mutex> lock(_mutex);
    _stream << out.str();
    _print(out.str());
}

std::string LogFile::getTime() {
    time_t rawtime;
    struct tm * timeinfo;
    char buffer[80];

    time (&rawtime);
    timeinfo = localtime(&rawtime);
    strftime(buffer, 80, "%d-%b-%Y %Hh%Mm%Ss", timeinfo);

    return std::string(buffer);
}

void LogFile::print(std::string str) {
    std::unique_lock<std::mutex> lock(_mutex);
    _print(str);
}

void LogFile::_print(std::string str) {
    if (_isWritingToConsole) {
        std::cout << str;
        std::cout.flush();
    }
}

std::vector<char> LogFile::flush() {
    _mutex.lock();
    std::string str = _stream.str();
    std::vector<char> data(str.begin(), str.end()); 
    _mutex.unlock();
    clear();
    return data;
}
