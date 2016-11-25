MODULE  = cxx_linalg

SRC_DIR = src
OUT_DIR = ..
CPP_FILES = $(wildcard $(SRC_DIR)/*.cpp)
H_FILES = $(wildcard $(SRC_DIR)/*.h)

CXXFLAGS  = -Wall -shared -fPIC 
INCLUDES  = -I/usr/include/python2.7/
LIBS	  = -Lbin -lboost_python -lgmp -lgmpxx

all: $(MODULE)

$(MODULE): $(CPP_FILES) $(H_FILES)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(CPP_FILES) $(LIBS) -o $@.so
	mv $@.so $(OUT_DIR)

clean:
	rm $(OUT_DIR)/$(MODULE).so
	
