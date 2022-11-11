from setuptools import setup

import os, shutil

setup()


# Create settings environment #
settingsDir: str = os.path.join(os.getenv("PYPICKUP_INDEX_PATH"), "settings")

if os.path.exists(settingsDir):
    shutil.rmtree(settingsDir)
os.makedirs(settingsDir)

wheelFiltersSettings_FileName: str = "wheelFiltersSettings.yaml"
wheelFiltersSettings_OriginalPath: str = os.path.join("./pypickup/settings/", wheelFiltersSettings_FileName)
if os.path.isfile(wheelFiltersSettings_OriginalPath):
    wheelFilterSettings_UserFile = os.path.join(settingsDir, wheelFiltersSettings_FileName)

    if not os.path.isfile(wheelFilterSettings_UserFile):
        shutil.copyfile(wheelFiltersSettings_OriginalPath, wheelFilterSettings_UserFile)