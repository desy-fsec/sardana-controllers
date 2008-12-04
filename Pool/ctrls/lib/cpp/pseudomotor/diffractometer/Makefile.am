RSYNC_OPTS = -r --cvs-exclude

install-data-local:
	rsync $(RSYNC_OPTS) $(srcdir)/*.png $(pkglibdir)

if USE_PARENT_AS_POOL_PATH
    CTRL_ROOT = $(top_srcdir)/..
else
    CTRL_ROOT = @POOL_ROOT@
endif 

pkglib_LTLIBRARIES = Diffractometer.la

AM_CPPFLAGS = -I@TANGO_ROOT@/include \
		-I@OMNI_ROOT@/include \
		$(PYTHON_CPPFLAGS) \
		-I$(CTRL_ROOT)/include \
		-I@HKL_ROOT@/include	
				 
AM_CXXFLAGS = -DREENTRANT 
AM_LDFLAGS = -module -avoid-version

Diffractometer_la_LIBADD = -L@HKL_ROOT@/lib \
		-lhkl

Diffractometer_la_SOURCES = $(srcdir)/Diffrac.h \
					$(srcdir)/Diffrac.cpp \
					$(srcdir)/Diffrac2C.h \
					$(srcdir)/Diffrac2C.cpp \
					$(srcdir)/Diffrac4C.h \
					$(srcdir)/Diffrac4C.cpp \
					$(srcdir)/Diffrac6C.h \
					$(srcdir)/Diffrac6C.cpp \
					$(srcdir)/Diffraction.cpp 

dist-hook:
	cp $(srcdir)/*.png $(distdir)			
