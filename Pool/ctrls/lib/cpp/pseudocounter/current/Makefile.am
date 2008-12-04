RSYNC_OPTS = -r --cvs-exclude

install-data-local:
	rsync $(RSYNC_OPTS) $(srcdir)/*.png $(pkglibdir)

if USE_PARENT_AS_POOL_PATH
    CTRL_ROOT = $(top_srcdir)/..
else
    CTRL_ROOT = @POOL_ROOT@
endif 


pkglib_LTLIBRARIES = CurrentPseudoCoCtrl.la

AM_CPPFLAGS = -I@TANGO_ROOT@/include \
			-I@OMNI_ROOT@/include \
			$(PYTHON_CPPFLAGS) \
			-I$(CTRL_ROOT)/include
				 
AM_CXXFLAGS = -DREENTRANT 
AM_LDFLAGS = -module -avoid-version

CurrentPseudoCoCtrl_la_SOURCES = $(srcdir)/CurrentPseudoCoCtrl.cpp \
					$(srcdir)/CurrentPseudoCoCtrl.h
					
dist-hook:
	cp $(srcdir)/*.png $(distdir)
