from __future__ import print_function

import os
import sqlite3
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import hou

try:
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *
except:
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *

DBFILE = r'\\File-share\temp\review.db'

scriptTemplate = u'''<?xml version="1.0" encoding="UTF-8"?>
<shelfDocument>
  <!-- This file contains definitions of shelves, toolbars, and tools.
 It should not be hand-edited when it is being used by the application.
 Note, that two definitions of the same element are not allowed in
 a single file. -->

  <tool name="$HDA_DEFAULT_TOOL" label="$HDA_LABEL" icon="$HDA_ICON">
    <toolMenuContext name="viewer">
      <contextNetType>OBJ</contextNetType>
    </toolMenuContext>
    <toolMenuContext name="network">
      <contextOpType>$HDA_TABLE_AND_NAME</contextOpType>
    </toolMenuContext>
    <toolSubmenu>{0}</toolSubmenu>
    <script scriptType="python"><![CDATA[import objecttoolutils

objecttoolutils.genericTool(kwargs, "$HDA_NAME")]]></script>
  </tool>
</shelfDocument>'''


class SubnetToAsset(QDialog):
    def __init__(self, subnet, parent=None):
        super(SubnetToAsset, self).__init__(parent)
        self.subnet = subnet

        self.setWindowTitle('Subnet to Asset')

        self.assetProject = QComboBox()
        with sqlite3.connect(DBFILE) as db:
            c = db.cursor()
            c.execute('SELECT name, id FROM project ORDER BY id DESC;')
            projects = c.fetchall()
        for name, num in projects:
            self.assetProject.addItem(name.title(), num)

        self.assetName = QLineEdit()
        self.assetName.setPlaceholderText('Asset name')
        self.assetName.setText(subnet.name())

        self.assetLabel = QLineEdit()
        self.assetLabel.setPlaceholderText('Asset label')

        self.assetCatalogLabel = QLineEdit()
        self.assetCatalogLabel.setPlaceholderText('Label in Catalog')

        self.assetClass = QComboBox()
        with sqlite3.connect(DBFILE) as db:
            c = db.cursor()
            c.execute('SELECT name, label, id FROM class ORDER BY name ASC;')
            classes = c.fetchall()
        for name, label, num in classes:
            self.assetClass.addItem(QIcon(os.path.join(r'\\file-share\temp\Asset_icons', name + '.svg')),
                                    '{0} ({1})'.format(name, label), (num, name))

        self.pickColorButton = QPushButton()
        self.pickColorButton.setStyleSheet('background: rgb(230, 230, 230);')
        self.pickColorButton.clicked.connect(self.pickColor)

        self.pathEdit = QLineEdit(os.path.dirname(hou.hipFile.path()))
        self.changePathButton = QToolButton()
        self.changePathButton.clicked.connect(self.selectPath)
        pathLayout = QHBoxLayout()
        pathLayout.addWidget(self.pathEdit)
        pathLayout.addWidget(self.changePathButton)

        self.buildButton = QPushButton('Build')
        self.buildButton.clicked.connect(self.buildAsset)

        spacerItem = QSpacerItem(0, 0, QSizePolicy.Ignored, QSizePolicy.Expanding)

        QVBoxLayout(self)

        self.layout().addWidget(self.assetProject)
        self.layout().addWidget(self.assetName)
        self.layout().addWidget(self.assetLabel)
        self.layout().addWidget(self.assetCatalogLabel)
        self.layout().addWidget(self.assetClass)
        self.layout().addWidget(self.pickColorButton)
        self.layout().addLayout(pathLayout)
        self.layout().addWidget(self.buildButton)
        self.layout().addSpacerItem(spacerItem)

        self.nodeColor = QColor(230, 230, 230)

    def selectPath(self):
        self.pathEdit.setText(
            QFileDialog.getExistingDirectory(self, 'Select Path', self.pathEdit.text(), QFileDialog.DirectoryOnly))

    def buildAsset(self):
        name = '{project}::{name}::1.0'.format(project=self.assetProject.currentText().lower(),
                                               name=self.assetName.text().lower())
        filepath = os.path.join(self.pathEdit.text(), name.replace(':', '_').replace('.', '_') + '.hda')
        msg = 'Asset name: {assetName}\n' \
              'Filepath: {filePath}'.format(assetName=name, filePath=filepath)
        reply = QMessageBox.question(self, 'Building Confirm', msg, QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            parmTemplateGroup = self.subnet.parmTemplateGroup()

            asset = self.subnet.createDigitalAsset(name, filepath, self.assetLabel.text(), 0, 1, True, '',
                                                   ignore_external_references=True)
            assetDef = asset.type().definition()
            assetDef.addSection('OnCreated', 'kwargs["node"].setUserData("nodeshape", "tilted")'
                                             '\nkwargs["node"].setColor(hou.Color({0}, {1}, {2}))'.format(
                self.nodeColor.redF(), self.nodeColor.greenF(), self.nodeColor.blueF()))
            assetDef.setExtraFileOption('OnCreated/IsPython', True)
            assetDef.addSection('PythonModule', 'from Studio import *')
            assetDef.setExtraFileOption('PythonModule/IsPython', True)
            assetDef.setParmTemplateGroup(parmTemplateGroup)
            assetDef.setIcon(r'//file-share/temp/Asset_icons/' + self.assetClass.currentData()[1] + '.svg')
            newText = scriptTemplate.format('Studio Assets')
            assetDef.addSection('Tools.shelf', newText)
            # create parm template
            houParmTemplate = hou.FolderParmTemplate("stdswitcher3_2", "Studio", folder_type=hou.folderType.Tabs,
                                                     default_value=0, ends_tab_group=False)
            houParmTemplate2 = hou.LabelParmTemplate("labelparm6", "emptySpace", column_labels=([""]))
            houParmTemplate2.hideLabel(True)
            houParmTemplate2.setJoinWithNext(True)
            houParmTemplate.addParmTemplate(houParmTemplate2)
            houParmTemplate2 = hou.ButtonParmTemplate("history", "Show History")
            houParmTemplate2.setJoinWithNext(True)
            houParmTemplate2.setScriptCallback("kwargs['node'].hdaModule().showHistory(kwargs)")
            houParmTemplate2.setScriptCallbackLanguage(hou.scriptLanguage.Python)
            houParmTemplate2.setTags({"script_callback": "kwargs['node'].hdaModule().showHistory(kwargs)",
                                      "script_callback_language": "python"})
            houParmTemplate.addParmTemplate(houParmTemplate2)
            houParmTemplate2 = hou.LabelParmTemplate("labelparm2", "emptySpace", column_labels=([""]))
            houParmTemplate2.hideLabel(True)
            houParmTemplate.addParmTemplate(houParmTemplate2)
            houParmTemplate2 = hou.LabelParmTemplate("labelparm7", "emptySpace", column_labels=([""]))
            houParmTemplate2.hideLabel(True)
            houParmTemplate2.setJoinWithNext(True)
            houParmTemplate.addParmTemplate(houParmTemplate2)
            houParmTemplate2 = hou.ButtonParmTemplate("inc_version", "Increment Version")
            houParmTemplate2.setJoinWithNext(True)
            houParmTemplate2.setScriptCallback("hou.pwd().hdaModule().incrementVersion(kwargs)")
            houParmTemplate2.setScriptCallbackLanguage(hou.scriptLanguage.Python)
            houParmTemplate2.setTags({"script_callback": "hou.pwd().hdaModule().incrementVersion(kwargs)",
                                      "script_callback_language": "python"})
            houParmTemplate.addParmTemplate(houParmTemplate2)
            houParmTemplate2 = hou.LabelParmTemplate("labelparm3", "emptySpace", column_labels=([""]))
            houParmTemplate2.hideLabel(True)
            houParmTemplate.addParmTemplate(houParmTemplate2)
            houParmTemplate2 = hou.LabelParmTemplate("labelparm8", "emptySpace", column_labels=([""]))
            houParmTemplate2.hideLabel(True)
            houParmTemplate2.setJoinWithNext(True)
            houParmTemplate.addParmTemplate(houParmTemplate2)
            houParmTemplate2 = hou.ButtonParmTemplate("review", "Publish")
            houParmTemplate2.setJoinWithNext(True)
            houParmTemplate2.setScriptCallback("kwargs['node'].hdaModule().publishAsset(kwargs)")
            houParmTemplate2.setScriptCallbackLanguage(hou.scriptLanguage.Python)
            houParmTemplate2.setTags({"script_callback": "kwargs['node'].hdaModule().publishAsset(kwargs)",
                                      "script_callback_language": "python"})
            houParmTemplate.addParmTemplate(houParmTemplate2)
            houParmTemplate2 = hou.LabelParmTemplate("labelparm4", "emptySpace", column_labels=([""]))
            houParmTemplate2.hideLabel(True)
            houParmTemplate.addParmTemplate(houParmTemplate2)

            templateGroup = assetDef.parmTemplateGroup()
            templateGroup.addParmTemplate(houParmTemplate)
            assetDef.setParmTemplateGroup(templateGroup)
            asset.setColor(hou.Color(self.nodeColor.redF(), self.nodeColor.greenF(), self.nodeColor.blueF()))
            asset.setUserData("nodeshape", "tilted")
            asset.matchCurrentDefinition()
            self.close()

    def pickColor(self):
        self.nodeColor = QColorDialog.getColor(QColor(230, 230, 230), self, 'Node Color')
        self.pickColorButton.setStyleSheet(
            'background: rgb({r}, {g}, {b});'.format(r=self.nodeColor.red(),
                                                     g=self.nodeColor.green(),
                                                     b=self.nodeColor.blue()))


selectedNodes = hou.selectedNodes()
if selectedNodes and selectedNodes[0].canCreateDigitalAsset():
    window = SubnetToAsset(selectedNodes[0], hou.qt.mainWindow())
    window.exec_()
