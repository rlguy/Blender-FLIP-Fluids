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

#include "particlesystem.h"


ParticleSystem::ParticleSystem() {
}

void ParticleSystem::update() {
    size_t size = evaluateSize();
    _expandVectors(_charAttributes, _charDefaults, size);
    _expandVectors(_ucharAttributes, _ucharDefaults, size);
    _expandVectors(_boolAttributes, _boolDefaults, size);
    _expandVectors(_intAttributes, _intDefaults, size);
    _expandVectors(_idAttributes, _idDefaults, size);
    _expandVectors(_floatAttributes, _floatDefaults, size);
    _expandVectors(_vector3Attributes, _vector3Defaults, size);
    _size = size;
}

size_t ParticleSystem::evaluateSize() {
    size_t size = 0;
    size = std::max(size, _getMaxVectorSize(_charAttributes));
    size = std::max(size, _getMaxVectorSize(_ucharAttributes));
    size = std::max(size, _getMaxVectorSize(_boolAttributes));
    size = std::max(size, _getMaxVectorSize(_intAttributes));
    size = std::max(size, _getMaxVectorSize(_idAttributes));
    size = std::max(size, _getMaxVectorSize(_floatAttributes));
    size = std::max(size, _getMaxVectorSize(_vector3Attributes));
    return size;
}

bool ParticleSystem::empty() {
    return evaluateSize() == 0;
}

void ParticleSystem::resize(size_t n) {
    _resizeVectors(_charAttributes, n);
    _resizeVectors(_ucharAttributes, n);
    _resizeVectors(_boolAttributes, n);
    _resizeVectors(_intAttributes, n);
    _resizeVectors(_idAttributes, n);
    _resizeVectors(_floatAttributes, n);
    _resizeVectors(_vector3Attributes, n);
    update();
}

void ParticleSystem::reserve(size_t n) {
    _reserveVectors(_charAttributes, n);
    _reserveVectors(_ucharAttributes, n);
    _reserveVectors(_boolAttributes, n);
    _reserveVectors(_intAttributes, n);
    _reserveVectors(_idAttributes, n);
    _reserveVectors(_floatAttributes, n);
    _reserveVectors(_vector3Attributes, n);
}

void ParticleSystem::removeParticles(std::vector<bool> &toRemove) {
    _removeParticlesFromVectorList(_charAttributes, toRemove);
    _removeParticlesFromVectorList(_ucharAttributes, toRemove);
    _removeParticlesFromVectorList(_boolAttributes, toRemove);
    _removeParticlesFromVectorList(_intAttributes, toRemove);
    _removeParticlesFromVectorList(_idAttributes, toRemove);
    _removeParticlesFromVectorList(_floatAttributes, toRemove);
    _removeParticlesFromVectorList(_vector3Attributes, toRemove);
    update();
}

void ParticleSystem::printParticle(size_t index) {
    for (size_t aidx = 0; aidx < _attributes.size(); aidx++) {
        ParticleSystemAttribute att = _attributes[aidx];

        switch (att.type) {
            case AttributeDataType::CHAR:
                {
                    char value = _charAttributes[att.id][index];
                    std::cout << att.name << " \t" << (int)value << std::endl;
                    break;
                }
            case AttributeDataType::UCHAR:
                {
                    unsigned char value = _ucharAttributes[att.id][index];
                    std::cout << att.name << " \t" << (int)value << std::endl;
                    break;
                }
            case AttributeDataType::BOOL:
                {
                    bool value = _boolAttributes[att.id][index];
                    std::cout << att.name << " \t" << value << std::endl;
                    break;
                }
            case AttributeDataType::INT:
                {
                    int value = _intAttributes[att.id][index];
                    std::cout << att.name << " \t" << value << std::endl;
                    break;
                }
            case AttributeDataType::ID:
                {
                    size_t value = _idAttributes[att.id][index];
                    std::cout << att.name << " \t" << value << std::endl;
                    break;
                }
            case AttributeDataType::FLOAT:
                {
                    float value = _floatAttributes[att.id][index];
                    std::cout << att.name << " \t" << value << std::endl;
                    break;
                }
            case AttributeDataType::VECTOR3:
                {
                    vmath::vec3 value = _vector3Attributes[att.id][index];
                    std::cout << att.name << " \t" << value << std::endl;
                    break;
                }
            default:
                std::cout << "Error: Undefined Attribute \t" << att.name << std::endl; 
                break;
        }
    }
}

bool ParticleSystem::isSchemaEqual(ParticleSystem &other, bool strict) {
    std::vector<ParticleSystemAttribute> otherAttributes = other.getAttributes();
    if (this->_attributes.size() != otherAttributes.size()) {
        return false;
    }

    for (size_t i = 0; i < _attributes.size(); i++) {
        if (strict) {
            if (_attributes[i] != otherAttributes[i]) {
                return false;
            }
        } else {
            ParticleSystemAttribute thisAtt = _attributes[i];
            ParticleSystemAttribute otherAtt = other.getAttribute(thisAtt.name);
            if (thisAtt.name != otherAtt.name || thisAtt.type != otherAtt.type) {
                return false;
            }
        }
    }

    for (size_t i = 0; i < _attributes.size(); i++) {
        ParticleSystemAttribute thisAtt = _attributes[i];
        ParticleSystemAttribute otherAtt = other.getAttribute(thisAtt.name);

        float eps = 1e-6;
        switch (thisAtt.type) {
            case AttributeDataType::CHAR:
                {
                    char *thisDefault, *otherDefault;
                    getAttributeDefault(thisAtt, thisDefault);
                    other.getAttributeDefault(otherAtt, otherDefault);
                    if (*thisDefault != *otherDefault) {
                        return false;
                    }
                    break;
                }
            case AttributeDataType::UCHAR:
                {
                    unsigned char *thisDefault, *otherDefault;
                    getAttributeDefault(thisAtt, thisDefault);
                    other.getAttributeDefault(otherAtt, otherDefault);
                    if (*thisDefault != *otherDefault) {
                        return false;
                    }
                    break;
                }
            case AttributeDataType::BOOL:
                {
                    bool *thisDefault, *otherDefault;
                    getAttributeDefault(thisAtt, thisDefault);
                    other.getAttributeDefault(otherAtt, otherDefault);
                    if (*thisDefault != *otherDefault) {
                        return false;
                    }
                    break;
                }
            case AttributeDataType::INT:
                {
                    int *thisDefault, *otherDefault;
                    getAttributeDefault(thisAtt, thisDefault);
                    other.getAttributeDefault(otherAtt, otherDefault);
                    if (*thisDefault != *otherDefault) {
                        return false;
                    }
                    break;
                }
            case AttributeDataType::ID:
                {
                    size_t *thisDefault, *otherDefault;
                    getAttributeDefault(thisAtt, thisDefault);
                    other.getAttributeDefault(otherAtt, otherDefault);
                    if (*thisDefault != *otherDefault) {
                        return false;
                    }
                    break;
                }
            case AttributeDataType::FLOAT:
                {
                    float *thisDefault, *otherDefault;
                    getAttributeDefault(thisAtt, thisDefault);
                    other.getAttributeDefault(otherAtt, otherDefault);
                    if (std::abs(*thisDefault - *otherDefault) > eps) {
                        return false;
                    }
                    break;
                }
            case AttributeDataType::VECTOR3:
                {
                    vmath::vec3 *thisDefault, *otherDefault;
                    getAttributeDefault(thisAtt, thisDefault);
                    other.getAttributeDefault(otherAtt, otherDefault);
                    if (vmath::length(*thisDefault - *otherDefault) > eps) {
                        return false;
                    }
                    break;
                }
            default:
                {
                    break;
                }
        }

    }

    return true;
}

ParticleSystem ParticleSystem::generateEmptyCopy() {
    ParticleSystem newSystem;

    for (size_t i = 0; i < _attributes.size(); i++) {
        ParticleSystemAttribute att = _attributes[i];
    
        switch (att.type) {
            case AttributeDataType::CHAR:
                {
                    char *def;
                    getAttributeDefault(att, def);
                    newSystem.addAttributeChar(att.name, *def);
                    break;
                }
            case AttributeDataType::UCHAR:
                {
                    unsigned char *def;
                    getAttributeDefault(att, def);
                    newSystem.addAttributeUChar(att.name, *def);
                    break;
                }
            case AttributeDataType::BOOL:
                {
                    bool *def;
                    getAttributeDefault(att, def);
                    newSystem.addAttributeBool(att.name, *def);
                    break;
                }
            case AttributeDataType::INT:
                {
                    int *def;
                    getAttributeDefault(att, def);
                    newSystem.addAttributeInt(att.name, *def);
                    break;
                }
            case AttributeDataType::ID:
                {
                    size_t *def;
                    getAttributeDefault(att, def);
                    newSystem.addAttributeID(att.name, *def);
                    break;
                }
            case AttributeDataType::FLOAT:
                {
                    float *def;
                    getAttributeDefault(att, def);
                    newSystem.addAttributeFloat(att.name, *def);
                    break;
                }
            case AttributeDataType::VECTOR3:
                {
                    vmath::vec3 *def;
                    getAttributeDefault(att, def);
                    newSystem.addAttributeVector3(att.name, *def);
                    break;
                }
            default:
                {
                    std::string msg = "Error: Invalid ParticleSystemAttribute in generateEmptyCopy()";
                    msg += " <id=" + _toString(att.id) + ",";
                    msg += " name=" + att.name + ",";
                    msg += " type=" + _toString((int)att.type) + ">\n";
                    throw std::runtime_error(msg);
                    break;
                }
        }
    }

    return newSystem;
}

void ParticleSystem::merge(ParticleSystem &other) {
    FLUIDSIM_ASSERT(isSchemaEqual(other));

    update();
    other.update();
    _mergeVectors(_charAttributes, other._charAttributes);
    _mergeVectors(_ucharAttributes, other._ucharAttributes);
    _mergeVectors(_boolAttributes, other._boolAttributes);
    _mergeVectors(_intAttributes, other._intAttributes);
    _mergeVectors(_idAttributes, other._idAttributes);
    _mergeVectors(_floatAttributes, other._floatAttributes);
    _mergeVectors(_vector3Attributes, other._vector3Attributes);
    update();
}

ParticleSystemAttribute ParticleSystem::addAttributeChar(std::string name, char defaultValue) {
    ParticleSystemAttribute att;
    att.id = _charAttributes.size();
    att.name = name;
    att.type = AttributeDataType::CHAR;

    _attributes.push_back(att);
    _charAttributes.push_back(std::vector<char>());
    _charDefaults.push_back(defaultValue);

    return att;
}

ParticleSystemAttribute ParticleSystem::addAttributeUChar(std::string name, unsigned char defaultValue) {
    ParticleSystemAttribute att;
    att.id = _ucharAttributes.size();
    att.name = name;
    att.type = AttributeDataType::UCHAR;

    _attributes.push_back(att);
    _ucharAttributes.push_back(std::vector<unsigned char>());
    _ucharDefaults.push_back(defaultValue);

    return att;
}

ParticleSystemAttribute ParticleSystem::addAttributeBool(std::string name, bool defaultValue) {
    ParticleSystemAttribute att;
    att.id = _boolAttributes.size();
    att.name = name;
    att.type = AttributeDataType::BOOL;

    _attributes.push_back(att);
    _boolAttributes.push_back(std::vector<bool>());
    _boolDefaults.push_back(defaultValue);

    return att;
}

ParticleSystemAttribute ParticleSystem::addAttributeInt(std::string name, int defaultValue) {
    ParticleSystemAttribute att;
    att.id = _intAttributes.size();
    att.name = name;
    att.type = AttributeDataType::INT;

    _attributes.push_back(att);
    _intAttributes.push_back(std::vector<int>());
    _intDefaults.push_back(defaultValue);

    return att;
}

ParticleSystemAttribute ParticleSystem::addAttributeID(std::string name, size_t defaultValue) {
    ParticleSystemAttribute att;
    att.id = _idAttributes.size();
    att.name = name;
    att.type = AttributeDataType::ID;

    _attributes.push_back(att);
    _idAttributes.push_back(std::vector<size_t>());
    _idDefaults.push_back(defaultValue);

    return att;
}

ParticleSystemAttribute ParticleSystem::addAttributeFloat(std::string name, float defaultValue) {
    ParticleSystemAttribute att;
    att.id = _floatAttributes.size();
    att.name = name;
    att.type = AttributeDataType::FLOAT;

    _attributes.push_back(att);
    _floatAttributes.push_back(std::vector<float>());
    _floatDefaults.push_back(defaultValue);

    return att;
}

ParticleSystemAttribute ParticleSystem::addAttributeVector3(std::string name, vmath::vec3 defaultValue) {
    ParticleSystemAttribute att;
    att.id = _vector3Attributes.size();
    att.name = name;
    att.type = AttributeDataType::VECTOR3;

    _attributes.push_back(att);
    _vector3Attributes.push_back(std::vector<vmath::vec3>());
    _vector3Defaults.push_back(defaultValue);

    return att;
}

std::vector<char> *ParticleSystem::getAttributeValuesChar(ParticleSystemAttribute &att) {
    _validateAttribute(att);
    return &(_charAttributes[att.id]);
}

std::vector<char> *ParticleSystem::getAttributeValuesChar(std::string name) {
    ParticleSystemAttribute att = _getAttributeByName(name);
    return getAttributeValuesChar(att);
}

std::vector<unsigned char> *ParticleSystem::getAttributeValuesUChar(ParticleSystemAttribute &att) {
    _validateAttribute(att);
    return &(_ucharAttributes[att.id]);
}

std::vector<unsigned char> *ParticleSystem::getAttributeValuesUChar(std::string name) {
    ParticleSystemAttribute att = _getAttributeByName(name);
    return getAttributeValuesUChar(att);
}

std::vector<bool> *ParticleSystem::getAttributeValuesBool(ParticleSystemAttribute &att) {
    _validateAttribute(att);
    return &(_boolAttributes[att.id]);
}

std::vector<bool> *ParticleSystem::getAttributeValuesBool(std::string name) {
    ParticleSystemAttribute att = _getAttributeByName(name);
    return getAttributeValuesBool(att);
}

std::vector<int> *ParticleSystem::getAttributeValuesInt(ParticleSystemAttribute &att) {
    _validateAttribute(att);
    return &(_intAttributes[att.id]);
}

std::vector<int> *ParticleSystem::getAttributeValuesInt(std::string name) {
    ParticleSystemAttribute att = _getAttributeByName(name);
    return getAttributeValuesInt(att);
}

std::vector<size_t> *ParticleSystem::getAttributeValuesID(ParticleSystemAttribute &att) {
    _validateAttribute(att);
    return &(_idAttributes[att.id]);
}

std::vector<size_t> *ParticleSystem::getAttributeValuesID(std::string name) {
    ParticleSystemAttribute att = _getAttributeByName(name);
    return getAttributeValuesID(att);
}

std::vector<float> *ParticleSystem::getAttributeValuesFloat(ParticleSystemAttribute &att) {
    _validateAttribute(att);
    return &(_floatAttributes[att.id]);
}

std::vector<float> *ParticleSystem::getAttributeValuesFloat(std::string name) {
    ParticleSystemAttribute att = _getAttributeByName(name);
    return getAttributeValuesFloat(att);
}

std::vector<vmath::vec3> *ParticleSystem::getAttributeValuesVector3(ParticleSystemAttribute &att) {
    _validateAttribute(att);
    return &(_vector3Attributes[att.id]);
}

std::vector<vmath::vec3> *ParticleSystem::getAttributeValuesVector3(std::string name) {
    ParticleSystemAttribute att = _getAttributeByName(name);
    return getAttributeValuesVector3(att);
}


ParticleSystemAttribute ParticleSystem::_getAttributeByName(std::string name) {
    for (size_t i = 0; i < _attributes.size(); i++) {
        if (_attributes[i].name == name) {
            return _attributes[i];
        }
    }

    ParticleSystemAttribute blank;
    blank.id = -1;
    blank.name = name;
    blank.type = AttributeDataType::UNDEFINED;

    return blank;
}

void ParticleSystem::_validateAttribute(ParticleSystemAttribute &att) {
    if (att.id < 0) {
        std::string msg = "Error: Invalid ParticleSystemAttribute";
        msg += " <id=" + _toString(att.id) + ",";
        msg += " name=" + att.name + ",";
        msg += " type=" + _toString((int)att.type) + ">\n";
        throw std::runtime_error(msg);
    }
}