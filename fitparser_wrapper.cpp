#include "fitparser_wrapper.h"
#include "treemodel.h"
#include "ffsparser.h"
#include "fitparser.h"
#include "basetypes.h"
#include "ubytearray.h"

#include <fstream>
#include <sstream>
#include <iostream>

class FitParserWrapperImpl {
public:
    TreeModel model;
    FfsParser ffsParser;
    FitParser fitParser;

    UByteArray fileData;

    FitParserWrapperImpl() : ffsParser(&model), fitParser(&model, &ffsParser) {}

    bool loadFile(const std::string &path) {
        std::ifstream file(path, std::ios::binary);
        if (!file) return false;

        std::ostringstream ss;
        ss << file.rdbuf();
        fileData = UByteArray(ss.str().c_str(), (UINT32)ss.str().size());

        // Parse file into model
        return ffsParser.parse(fileData) == U_SUCCESS;
    }

    std::string parse() {
        fitParser.clearMessages();
        fitParser.parseFit(model.index(0, 0)); // root index
        return toUTF8(fitParser.getSecurityInfo());
    }

    std::string getSecurity() {
        return toUTF8(fitParser.getSecurityInfo());
    }

    std::string toUTF8(const UString& s) {
        std::cerr << "[DEBUG] Length: " << s.slen << std::endl;

        return std::string(reinterpret_cast<const char*>(s.data), s.slen);
    }
 
    
};

FitParserWrapper::FitParserWrapper() {
    impl = new FitParserWrapperImpl();
}

FitParserWrapper::~FitParserWrapper() {
    delete static_cast<FitParserWrapperImpl*>(impl);
}

bool FitParserWrapper::loadFile(const std::string &path) {
    return static_cast<FitParserWrapperImpl*>(impl)->loadFile(path);
}

std::string FitParserWrapper::parseFitTable() {
    return static_cast<FitParserWrapperImpl*>(impl)->parse();
}

std::string FitParserWrapper::getSecurityInfo() {
    return static_cast<FitParserWrapperImpl*>(impl)->getSecurity();
}

