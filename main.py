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

        self.assetClass = QComboBox()
        with sqlite3.connect(DBFILE) as db:
            c = db.cursor()
            c.execute('SELECT name, label, id FROM class ORDER BY name ASC;')
            classes = c.fetchall()
        for name, label, num in classes:
            self.assetClass.addItem(QIcon(os.path.join(r'\\file-share\temp\Asset_icons', name.lower() + '.svg')),
                                    '{0} ({1})'.format(name, label), num)

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
        self.layout().addWidget(self.assetClass)
        self.layout().addLayout(pathLayout)
        self.layout().addWidget(self.buildButton)
        self.layout().addSpacerItem(spacerItem)

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

            asset = self.subnet.createDigitalAsset(name, filepath, self.assetLabel.text(), 0, 1, True, 'Hahahahahahhah',
                                                   ignore_external_references=True)
            assetDef = asset.type().definition()
            assetDef.addSection('OnCreated', 'hou.pwd().setUserData("nodeshape", "tilted")')

            assetDef.setParmTemplateGroup(parmTemplateGroup)
            newText = u'''<?xml version="1.0" encoding="UTF-8"?>
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
    <toolSubmenu>Models</toolSubmenu>
    <script scriptType="python"><![CDATA[import objecttoolutils

objecttoolutils.genericTool(kwargs, "$HDA_NAME")]]></script>
  </tool>
</shelfDocument>'''
            assetDef.addSection('Tools.shelf', newText)
            self.close()


selectedNodes = hou.selectedNodes()
if selectedNodes and selectedNodes[0].canCreateDigitalAsset():
    window = SubnetToAsset(selectedNodes[0], hou.qt.mainWindow())
    window.exec_()
