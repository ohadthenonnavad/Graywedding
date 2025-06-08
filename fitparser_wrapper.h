#ifndef FITPARSER_WRAPPER_H
#define FITPARSER_WRAPPER_H

#include <string>

class FitParserWrapper {
public:
    FitParserWrapper();
    ~FitParserWrapper();

    bool loadFile(const std::string &path);
    std::string parseFitTable();
    std::string getSecurityInfo();

private:
    void *impl; // forward-declared pointer to avoid exposing internals
};

#endif // FITPARSER_WRAPPER_H
