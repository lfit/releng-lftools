import os

def find_log_ini( file_name ):
  homedir = os.path.expanduser('~')
  if os.path.isfile('%s/.config/lftools/%s' % (homedir, file_name)):
      file_path=('%s/.config/lftools/%s' % (homedir, file_name))
  elif os.path.isfile('/etc/lftools/%s' % file_name):
      file_path=('/etc/lftools/%s' % file_name)
  else:
      file_path=('lftools/config/%s' % file_name)
  return file_path;

log_ini_file = "logging.ini"
log_ini_file_path = find_log_ini(log_ini_file)

print("Using logger config file: %s" % log_ini_file_path)
