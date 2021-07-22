TEMPLATE = app
CONFIG += console c++11
CONFIG -= app_bundle
CONFIG -= qt

INCLUDEPATH += /usr/include/
INCLUDEPATH += /usr/local/include

LIBS += -L"/usr/lib"
LIBS += -lwiringPi
LIBS += -lbcm2835
LIBS += -lcurl
LIBS += -pthread

SOURCES += \
        main.cpp \
    MFRC522.cpp \
    mfrc522_delegate.cpp \
    curlpostrequest.cpp

HEADERS += \
    # bcm2835.h \
    MFRC522.h \
    mfrc522_delegate.h \
    curlpostrequest.h
