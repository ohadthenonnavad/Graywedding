#ifndef FITPARSER_WRAPPER_H
#define FITPARSER_WRAPPER_H

#include "treemodel.h"
#include "treeitem.h"
#include "ffsparser.h"
#include "nvramparser.h"
#include "fitparser.h"
#include "basetypes.h"
#include "ubytearray.h"
#include "ustring.h"


#include <tuple>
#include <string>
#include <functional>


#include <fstream>
#include <map>
#include <sstream>
#include <iostream>


class FitParserWrapper {
public:
    FitParserWrapper();
    ~FitParserWrapper();

    bool loadFile(const std::string &path);
    std::string parseFitTable();
    std::string getSecurityInfo();
    std::tuple<size_t, size_t> getNvramRegion();
    std::map<std::string, std::string> parseNvramVars();
    std::pair<USTATUS, UString> parseNvarStoreWithInfo(const UModelIndex& index);



private:
    void *impl; // forward-declared pointer to avoid exposing internals
};

#endif // FITPARSER_WRAPPER_H
