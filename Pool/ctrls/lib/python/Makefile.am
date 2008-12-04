# Sardana device pool tango system

RSYNC_OPTS = -r --cvs-exclude

install-data-local:

	rsync $(RSYNC_OPTS) $(srcdir)/communication/* $(pythondir)
	rsync $(RSYNC_OPTS) $(srcdir)/countertimer/* $(pythondir)
	rsync $(RSYNC_OPTS) $(srcdir)/motor/* $(pythondir)
	rsync $(RSYNC_OPTS) $(srcdir)/pseudomotor/* $(pythondir)
	rsync $(RSYNC_OPTS) $(srcdir)/pseudocounter/* $(pythondir)
	rsync $(RSYNC_OPTS) $(srcdir)/zerod/* $(pythondir)
