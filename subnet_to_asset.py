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
except ImportError:
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *

REVIEW_DB = r'//FILE-SHARE_NEW/REVIEW/review.db'
CATALOG_DB = r'//FILE-SHARE_NEW/DATA/SHARED/catalog.db'
ASSET_CATEGORY_ICONS = r'//File-share_new/DATA/SHARED/asset_category_icons/'

scriptTemplate = u'''<?xml version="1.0" encoding="UTF-8"?>
<shelfDocument>
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
        with sqlite3.connect(CATALOG_DB) as catalog:
            c = catalog.cursor()
            c.execute('SELECT name, id FROM project ORDER BY id DESC;')
        for name, num in c.fetchall():
            self.assetProject.addItem(name.title(), num)

        self.assetName = QLineEdit()
        self.assetName.setPlaceholderText('Asset name')
        self.assetName.setText(subnet.name().lower())

        self.assetLabel = QLineEdit()
        self.assetLabel.setPlaceholderText('Asset label')
        self.assetLabel.setText(subnet.name().replace('_', ' ').title())

        self.assetCatalogLabel = QLineEdit()
        self.assetCatalogLabel.setPlaceholderText('Label in Catalog')

        self.assetClass = QComboBox()
        with sqlite3.connect(CATALOG_DB) as catalog:
            c = catalog.cursor()
            c.execute('SELECT label, local_label, id FROM category ORDER BY label ASC;')
            categories = c.fetchall()
        for name, label, num in categories:
            self.assetClass.addItem(QIcon(os.path.join(ASSET_CATEGORY_ICONS, name + '.svg')),
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

        mainLayout = QVBoxLayout(self)

        mainLayout.addWidget(self.assetProject)
        mainLayout.addWidget(self.assetName)
        mainLayout.addWidget(self.assetLabel)
        mainLayout.addWidget(self.assetCatalogLabel)
        mainLayout.addWidget(self.assetClass)
        mainLayout.addWidget(self.pickColorButton)
        mainLayout.addLayout(pathLayout)
        mainLayout.addWidget(self.buildButton)
        mainLayout.addSpacerItem(spacerItem)

        self.nodeColor = QColor(230, 230, 230)

    def selectPath(self):
        self.pathEdit.setText(
            QFileDialog.getExistingDirectory(self, 'Select Path', self.pathEdit.text(), QFileDialog.DirectoryOnly))

    def buildAsset(self):
        with sqlite3.connect(CATALOG_DB) as catalog:
            c = catalog.cursor()
            c.execute('SELECT COUNT(rowid) FROM asset WHERE label = ?', (self.assetName.text(),))
            data = c.fetchone()
            if data[0] != 0:
                self.close()
                return

        name = '{project}::{name}::1.0'.format(project=self.assetProject.currentText().lower(),
                                               name=self.assetName.text().lower())
        filepath = os.path.join(self.pathEdit.text(), name.replace(':', '_').replace('.', '_') + '.hda')
        msg = 'Asset name: {assetName}\n' \
              'Filepath: {filePath}'.format(assetName=name, filePath=filepath)
        reply = QMessageBox.question(self, 'Building Confirm', msg, QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            node = self.subnet.createDigitalAsset(name, filepath, self.assetLabel.text(), 0, 1, True, '',
                                                  ignore_external_references=True)

            # Node
            node.setColor(hou.Color(self.nodeColor.redF(), self.nodeColor.greenF(), self.nodeColor.blueF()))
            node.setUserData("nodeshape", "tilted")

            # Definition
            definition = node.type().definition()

            # Asset Category Name
            definition.setComment(self.assetClass.currentData(Qt.UserRole)[1])

            # Store Catalog Asset Name
            definition.setExtraFileOption('LocalLabel', self.assetCatalogLabel.text())

            # Store Asset Class
            definition.setExtraFileOption('AssetCategory', self.assetClass.currentData(Qt.UserRole)[0])

            # Manage Asset Button
            manageAssetButton = hou.ButtonParmTemplate('manage_asset', 'Manage Asset')
            manageAssetButton.setScriptCallbackLanguage(hou.scriptLanguage.Python)
            manageAssetButton.setScriptCallback('kwargs["node"].hdaModule().Studio.manageAsset(kwargs)')

            # Assemble parm templates
            parmTemplateGroup = definition.parmTemplateGroup()
            sourceTemplates = parmTemplateGroup.parmTemplates()
            if sourceTemplates:
                parmTemplateGroup.insertBefore(sourceTemplates[0], manageAssetButton)
            else:
                parmTemplateGroup.append(manageAssetButton)
            definition.setParmTemplateGroup(parmTemplateGroup)

            # OnCreated module
            definition.addSection('OnCreated', 'kwargs["node"].setUserData("nodeshape", "tilted")'
                                               '\nkwargs["node"].setColor(hou.Color({0}, {1}, {2}))'.format(
                self.nodeColor.redF(), self.nodeColor.greenF(), self.nodeColor.blueF()))
            definition.setExtraFileOption('OnCreated/IsPython', True)

            # PythonModule
            definition.addSection('PythonModule', 'import Studio')
            definition.setExtraFileOption('PythonModule/IsPython', True)

            # Icon
            definition.setIcon(os.path.join(ASSET_CATEGORY_ICONS, self.assetClass.currentData()[1] + '.svg'))

            # Tool Section
            definition.addSection('Tools.shelf', scriptTemplate.format('Studio Assets/Test'))

            # Finish
            node.matchCurrentDefinition()
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
