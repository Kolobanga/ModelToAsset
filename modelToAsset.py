import os
import sys
try:
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except:
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *


class ModelToAsset(QWidget):
    def __init__(self):
        super(ModelToAsset, self).__init__(None, Qt.WindowStaysOnTopHint)

        self.subnet = self.defineSubnet()
        self.setWindowTitle('Create HDA')
        self.resize(300, 250)

        self.projectNameLabel = QLabel('Chose Project Name:')
        self.project = QComboBox()
        self.project.addItems(['Kolobanga', 'Netski'])

        self.typeLabel = QLabel('Chose Project Type:')
        self.type = QComboBox()
        self.type.addItems(['Object', 'Scene'])

        self.assetName = QLineEdit()
        self.assetName.setPlaceholderText('Asset name')
        self.assetName.setText(self.subnet.name())

        self.assetLabel = QLineEdit()
        self.assetLabel.setPlaceholderText('Asset label')

        self.assetClass = QComboBox()
        self.assetClass.addItems(('Accessory',
                                  'Animal',
                                  'Building',
                                  'Character',
                                  'Clothes',
                                  'Device',
                                  'Food',
                                  'Furniture',
                                  'Object',
                                  'Plant',
                                  'Prop',
                                  'Tool',
                                  'Vehicle',
                                  'Weapon'))

        self.oldPath = os.path.splitext(hou.hipFile.path())[0] + '.hda'
        self.pathLine = QLineEdit(self.oldPath)
        self.changePathButton = QToolButton()
        self.changePathButton.clicked.connect(self.changePath)

        self.createButton = QPushButton('Create')
        self.createButton.clicked.connect(self.createAsset)

        QVBoxLayout(self)
        self.pathLayout = QHBoxLayout()
        self.pathLayout.addWidget(self.pathLine)
        self.pathLayout.addWidget(self.changePathButton)

        self.layout().addWidget(self.projectNameLabel)
        self.layout().addWidget(self.project)
        self.layout().addWidget(self.typeLabel)
        self.layout().addWidget(self.type)
        self.layout().addWidget(self.assetName)
        self.layout().addWidget(self.assetLabel)
        self.layout().addWidget(self.assetClass)
        self.layout().addLayout(self.pathLayout)
        self.layout().addWidget(self.createButton)

    def checkData(self):
        text = 'Project: {project}\nProject Type: {type}\n Asset Name: {assetName}\n Asset Label: {assetLabel} \n Asset Class: {assetClass}\n Path: {path}'.format(
            project=self.project.currentData(), type=self.type.currentData(), assetName=self.assetName.text(),
            assetLabel=self.assetLabel.text(), assetClass=self.assetClass.currentData(), path=self.pathLine.text())
        return hou.ui.displayMessage(text, buttons=('Cancel', 'Ok'), title='Confirm')

    def defineSubnet(self):
        nodes = hou.selectedNodes()
        if len(nodes) == 1 and nodes[0].canCreateDigitalAsset():
            return nodes[0]

    def changePath(self):
        self.pathLine.setText(hou.ui.selectFile(start_directory=self.oldPath, chooser_mode=hou.fileChooserMode.Write))

    def createAsset(self):
        if self.checkData() == 1:
            parmTemplateGroup = self.subnet.parmTemplateGroup()
            asset = self.subnet.createDigitalAsset(
                '{project}_{type}::{assetName}::1.0'.format(project=self.project.currentText(),
                                                            type=self.type.currentText(),
                                                            assetName=self.assetName.text()),
                self.pathLine.text(), self.assetLabel.text(), 0, 1, True, '', ignore_external_references=True)
            assetDef = asset.type().definition()

            assetDef.setParmTemplateGroup(parmTemplateGroup)
            # change tub submenu path
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModelToAsset()
    window.show()
    sys.exit(app.exec_())
