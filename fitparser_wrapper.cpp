#include "fitparser_wrapper.h"
#include "treemodel.h"
#include "treeitem.h"
#include "ffsparser.h"
#include "fitparser.h"
#include "basetypes.h"
#include "ubytearray.h"
#include "ustring.h"


#include <tuple>
#include <string>
#include <functional>


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


std::tuple<size_t, size_t> FitParserWrapper::getNvramRegion() {
    auto* implPtr = static_cast<FitParserWrapperImpl*>(impl);
    TreeModel* model = &implPtr->model;

    const UString targetGuid = UString("NVAR store");

    size_t foundOffset = 0;
    size_t foundSize = 0;

    std::function<void(UModelIndex)> recurse;
    recurse = [&](UModelIndex index) {
        if (!index.isValid()) return;

        // Create a new index pointing to the GUID column
        UModelIndex guidIndex = model->index(index.row(), 2, index.parent());
        UString guidText = model->text(guidIndex);
        std::string guidUtf8(reinterpret_cast<const char*>(guidText.data), guidText.slen);
        std::cout << "Checking GUID: " << guidUtf8 << std::endl;


        if (guidText == targetGuid) {
            foundOffset = model->offset(index);
            foundSize = 0;
            
            UModelIndex parent = index.parent();
            int row = index.row();
            int siblingCount = model->rowCount(parent);
            
            if (row + 1 < siblingCount) {
                UModelIndex nextSibling = model->index(row + 1, 0, parent);
                foundSize = model->offset(nextSibling) - foundOffset;
            } else {
                foundSize = implPtr->fileData.size() - foundOffset;
            }

            return;
        }

        const int rowCount = model->rowCount(index);
        for (int i = 0; i < rowCount; ++i) {
            UModelIndex child = model->index(i, 0, index);
            recurse(child);
            if (foundSize != 0) return; // early exit if found
        }
    };

    UModelIndex rootIndex = model->index(0, 0);
    recurse(rootIndex);

    return std::make_tuple(foundOffset, foundSize);
}



std::string FitParserWrapper::parseFitTable() {
    return static_cast<FitParserWrapperImpl*>(impl)->parse();
}

std::string FitParserWrapper::getSecurityInfo() {
    return static_cast<FitParserWrapperImpl*>(impl)->getSecurity();
}

