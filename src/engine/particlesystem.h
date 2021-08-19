/*
MIT License

Copyright (C) 2020 Ryan L. Guy

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

#ifndef FLUIDENGINE_PARTICLESYSTEM_H
#define FLUIDENGINE_PARTICLESYSTEM_H

#include <vector>
#include <string>
#include <sstream>
#include <stdexcept>

#include "vmath.h"
#include "fluidsimassert.h"


enum class AttributeDataType : char { 
    UNDEFINED = 0x00,
    CHAR = 0x01, 
    UCHAR = 0x02, 
    BOOL = 0x03,
    INT = 0x04,
    ID = 0x05,
    FLOAT = 0x06, 
    VECTOR3 = 0x07
};


struct ParticleSystemAttribute {
    int id = -1;
    std::string name;
    AttributeDataType type = AttributeDataType::UNDEFINED;

    bool operator== (const ParticleSystemAttribute &other) {
       return id == other.id && name == other.name && type == other.type;
    }

    bool operator!= (const ParticleSystemAttribute &other) {
       return !(*this == other);
    }
};


class ParticleSystem
{
public:
    ParticleSystem();

    void update();
    inline size_t size() { return _size; }
    bool empty();
    size_t evaluateSize();
    void resize(size_t n);
    void reserve(size_t n);
    void removeParticles(std::vector<bool> &toRemove);
    void printParticle(size_t index);

    std::vector<ParticleSystemAttribute> getAttributes() { return _attributes; }
    ParticleSystemAttribute getAttribute(std::string name) {return _getAttributeByName(name); }
    bool isSchemaEqual(ParticleSystem &other, bool strict=true);
    ParticleSystem generateEmptyCopy();
    void merge(ParticleSystem &other);

    ParticleSystemAttribute addAttributeChar(std::string name, char defaultValue=0x00);
    ParticleSystemAttribute addAttributeUChar(std::string name, unsigned char defaultValue=0x00);
    ParticleSystemAttribute addAttributeBool(std::string name, bool defaultValue=false);
    ParticleSystemAttribute addAttributeInt(std::string name, int defaultValue=0);
    ParticleSystemAttribute addAttributeID(std::string name, size_t defaultValue=-1);
    ParticleSystemAttribute addAttributeFloat(std::string name, float defaultValue=0.0f);
    ParticleSystemAttribute addAttributeVector3(std::string name, vmath::vec3 defaultValue=vmath::vec3());

    std::vector<char> *getAttributeValuesChar(ParticleSystemAttribute &att);
    std::vector<char> *getAttributeValuesChar(std::string name);

    std::vector<unsigned char> *getAttributeValuesUChar(ParticleSystemAttribute &att);
    std::vector<unsigned char> *getAttributeValuesUChar(std::string name);

    std::vector<bool> *getAttributeValuesBool(ParticleSystemAttribute &att);
    std::vector<bool> *getAttributeValuesBool(std::string name);

    std::vector<int> *getAttributeValuesInt(ParticleSystemAttribute &att);
    std::vector<int> *getAttributeValuesInt(std::string name);

    std::vector<size_t> *getAttributeValuesID(ParticleSystemAttribute &att);
    std::vector<size_t> *getAttributeValuesID(std::string name);

    std::vector<float> *getAttributeValuesFloat(ParticleSystemAttribute &att);
    std::vector<float> *getAttributeValuesFloat(std::string name);

    std::vector<vmath::vec3> *getAttributeValuesVector3(ParticleSystemAttribute &att);
    std::vector<vmath::vec3> *getAttributeValuesVector3(std::string name);

    template<class T>
    void getAttributeValues(ParticleSystemAttribute &att, std::vector<T> *&values) {
        FLUIDSIM_ASSERT(att.type != AttributeDataType::UNDEFINED);

        switch (att.type) {
            case AttributeDataType::CHAR:
                values = (std::vector<T>*)getAttributeValuesChar(att);
                break;
            case AttributeDataType::UCHAR:
                values = (std::vector<T>*)getAttributeValuesUChar(att);
                break;
            case AttributeDataType::BOOL:
                values = (std::vector<T>*)getAttributeValuesBool(att);
                break;
            case AttributeDataType::INT:
                values = (std::vector<T>*)getAttributeValuesInt(att);
                break;
            case AttributeDataType::ID:
                values = (std::vector<T>*)getAttributeValuesID(att);
                break;
            case AttributeDataType::FLOAT:
                values = (std::vector<T>*)getAttributeValuesFloat(att);
                break;
            case AttributeDataType::VECTOR3:
                values = (std::vector<T>*)getAttributeValuesVector3(att);
                break;
            default:
                {
                    std::string msg = "Error: Invalid ParticleSystemAttribute in getAttributeValues()";
                    msg += " <id=" + _toString(att.id) + ",";
                    msg += " name=" + att.name + ",";
                    msg += " type=" + _toString((int)att.type) + ">\n";
                    throw std::runtime_error(msg);
                    break;
                }
        }
    }

    template<class T>
    void getAttributeDefault(ParticleSystemAttribute &att, T *&value) {
        FLUIDSIM_ASSERT(att.type != AttributeDataType::UNDEFINED);

        switch (att.type) {
            case AttributeDataType::CHAR:
                value = (T*)&(_charDefaults[att.id]);
                break;
            case AttributeDataType::UCHAR:
                value = (T*)&(_ucharDefaults[att.id]);
                break;
            case AttributeDataType::BOOL:
                value = _boolDefaults[att.id] ? (T*)&_boolValueTrue : (T*)&_boolValueFalse;
                break;
            case AttributeDataType::INT:
                value = (T*)&(_intDefaults[att.id]);
                break;
            case AttributeDataType::ID:
                value = (T*)&(_idDefaults[att.id]);
                break;
            case AttributeDataType::FLOAT:
                value = (T*)&(_floatDefaults[att.id]);
                break;
            case AttributeDataType::VECTOR3:
                value = (T*)&(_vector3Defaults[att.id]);
                break;
            default:
                {
                    std::string msg = "Error: Invalid ParticleSystemAttribute in getAttributeDefault()";
                    msg += " <id=" + _toString(att.id) + ",";
                    msg += " name=" + att.name + ",";
                    msg += " type=" + _toString((int)att.type) + ">\n";
                    throw std::runtime_error(msg);
                    break;
                }
        }
    }

    template<class T>
    void getAttributeValues(std::string name, std::vector<T> *&values) {
        ParticleSystemAttribute att = _getAttributeByName(name);
        getAttributeValues(att, values);
    }

    template<class T>
    void addValues(ParticleSystemAttribute &att, std::vector<T> &values) {
        std::vector<T> *thisAttribute;
        getAttributeValues(att, thisAttribute);
        thisAttribute->insert(thisAttribute->end(), values.begin(), values.end());
    }

    template<class T>
    void addValues(std::string name, std::vector<T> &values) {
        ParticleSystemAttribute att = _getAttributeByName(name);
        addValues(att, values);
    }

private:

    ParticleSystemAttribute _getAttributeByName(std::string name);
    void _validateAttribute(ParticleSystemAttribute &att);

    template<class T>
    std::string _toString(T item) {
        std::ostringstream sstream;
        sstream << item;
        return sstream.str();
    }

    template<class T1, class T2>
    inline void _expandVectors(T1 &vectorList, T2 defaultList, size_t size) {
        for (size_t i = 0; i < vectorList.size(); i++) {
            if (vectorList[i].size() > size) {
                return;
            }
            vectorList[i].resize(size, defaultList[i]);
        }
    }

    template<class T>
    inline size_t _getMaxVectorSize(T &vectorList) {
        size_t size = 0;
        for (size_t i = 0; i < vectorList.size(); i++) {
            size = std::max(size, vectorList[i].size());
        }
        return size;
    }

    template<class T>
    inline void _resizeVectors(T &vectorList, size_t n) {
        for (size_t i = 0; i < vectorList.size(); i++) {
            vectorList[i].resize(n);
        }
    }

    template<class T>
    inline void _reserveVectors(T &vectorList, size_t n) {
        for (size_t i = 0; i < vectorList.size(); i++) {
            vectorList[i].reserve(n);
        }
    }

    template<class T>
    inline void _removeParticlesFromVector(T &vector, std::vector<bool> &toRemove) {
        FLUIDSIM_ASSERT(vector.size() == toRemove.size());

        int currentidx = 0;
        for (size_t i = 0; i < vector.size(); i++) {
            if (!toRemove[i]) {
                vector[currentidx] = vector[i];
                currentidx++;
            }
        }
        vector.resize(currentidx);
    }

    template<class T>
    inline void _removeParticlesFromVectorList(T &vectorList, std::vector<bool> &toRemove) {
        for (size_t i = 0; i < vectorList.size(); i++) {
            _removeParticlesFromVector(vectorList[i], toRemove);
        }
    }

    template<class T>
    inline void _mergeVectors(T &vectorList1, T &vectorList2) {
        for (size_t i = 0; i < vectorList1.size(); i++) {
            vectorList1[i].insert(vectorList1[i].end(), vectorList2[i].begin(), vectorList2[i].end());
        }
    }

    size_t _size = 0;

    std::vector<ParticleSystemAttribute> _attributes;

    std::vector<std::vector<char> > _charAttributes;
    std::vector<std::vector<unsigned char> > _ucharAttributes;
    std::vector<std::vector<bool> > _boolAttributes;
    std::vector<std::vector<int> > _intAttributes;
    std::vector<std::vector<size_t> > _idAttributes;
    std::vector<std::vector<float> > _floatAttributes;
    std::vector<std::vector<vmath::vec3> > _vector3Attributes;

    std::vector<char> _charDefaults;
    std::vector<unsigned char> _ucharDefaults;
    std::vector<bool> _boolDefaults;
    std::vector<int> _intDefaults;
    std::vector<size_t> _idDefaults;
    std::vector<float> _floatDefaults;
    std::vector<vmath::vec3> _vector3Defaults;

    std::string _defaultPositionName = "POSITION";
    std::string _defaultVelocityName = "VELOCITY";
    std::string _defaultDiffuseLifetimeName = "LIFETIME";
    std::string _defaultDiffuseTypeName = "TYPE";
    std::string _defaultDiffuseIDName = "ID";

    // Workaround to get pointer to a true/false bool due to
    // not being able to address an std::vector<bool>
    bool _boolValueTrue = true;
    bool _boolValueFalse = false;
};


#endif