import QtQuick
import QtQuick.Controls 
import QtQuick.Layouts
import QtQuick.Dialogs
import QtQuick.Controls.Material

ApplicationWindow {
    id: root
    visible: true
    width: 600
    height: 700
    title: qsTr("Servodoor")

    Material.theme: Material.Dark
    Material.accent: Material.Blue
    
    readonly property int fontSizeLarge: 24
    readonly property int fontSizeSmall: 18 

    // Port properties
    property list<string> serialPortNames: []
    property string openCloseButtonText: "open"
    property string portInfoText: ""

    // Door properties
    property int numDoors: 0
    property var doorNames: []
    property var doorChecks: []

    // Configuration properties
    property string configInfoText: ""
    property var loadButtonEnabled: false
    property string errorMessageText: ""
    property var errorMessageVisible: false

    signal openCloseButtonClicked(string port)
    signal doorSwitchClicked(int index, string name, bool checked)
    signal loadConfigFile(string config_file)

    TabBar {
        id: navBar
        width: parent.width
        TabButton {
            text: qsTr("Connect")
            font.pixelSize: fontSizeLarge 
        }
        TabButton {
            text: qsTr("Control")
            font.pixelSize: fontSizeLarge 
        }
        TabButton {
            text: qsTr("Config")
            font.pixelSize: fontSizeLarge 

        }
    }

    StackLayout {
        id: tabStack
        width: parent.width
        height: parent.height - navBar.height
        currentIndex: navBar.currentIndex
        anchors.bottom: parent.bottom

        Item {
            id: connectTab 
            Rectangle {
                anchors.fill: parent
                color: Material.background 
                Rectangle {
                    anchors.fill: parent
                    anchors.topMargin: 10
                    anchors.bottomMargin: 50 
                    anchors.leftMargin: 50 
                    anchors.rightMargin: 50 
                    color: Material.background 
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 30 
                        Rectangle {
                            Layout.fillWidth: true
                            height: 20
                            color: Material.background 
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Rectangle {
                                Layout.fillWidth: true
                                color: Material.background 
                            }
                            Text {
                                text: "Port"
                                font.pixelSize: fontSizeLarge 
                                Layout.rightMargin: 20
                                color: Material.foreground
                            }
                            ComboBox {
                                id: portComboBox
                                model: serialPortNames
                                Layout.fillWidth: true
                                Layout.preferredWidth: 100
                                font.pixelSize: fontSizeSmall
                            }
                            Button {
                                id: portOpenCloseButton
                                text: openCloseButtonText 
                                font.pixelSize: fontSizeLarge 
                                Layout.leftMargin: 20
                                onClicked: {backend.on_open_close_button(portComboBox.currentValue)}
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                color: Material.background 
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: Material.background 
                            TextArea {
                                id: portInfoTextArea
                                anchors.fill: parent
                                readOnly: false 
                                font.pixelSize: fontSizeSmall
                                text: portInfoText 
                            }
                        }
                    }
                }
            }
        }

        Item {
            id: controlTab 
            Rectangle {
                anchors.fill: parent
                color: Material.background 
                Rectangle {
                    anchors.fill: parent
                    anchors.topMargin: 10
                    anchors.bottomMargin: 80
                    anchors.leftMargin: 100
                    anchors.rightMargin: 80
                    color: Material.background 
                    ScrollView {
                        anchors.fill: parent
                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 30 
                            Rectangle {
                                Layout.fillWidth: true
                                height: 20
                                color: Material.background 
                            }
                            Repeater {
                                model: numDoors 
                                Layout.alignment: Qt.AlignHCenter
                                Switch {
                                    text: doorNames[index]
                                    checked:  doorChecks[index] 
                                    font.pixelSize: fontSizeLarge 
                                    onClicked: {backend.on_door_switch_clicked(index, doorNames[index], checked)}
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                color: Material.background 
                            }
                        }
                    }
                }
            }
        }
        Item {
            id: configTab 
            Rectangle {
                anchors.fill: parent
                color: Material.background 
                Rectangle {
                    anchors.fill: parent
                    anchors.topMargin: 50
                    anchors.bottomMargin: 50
                    anchors.leftMargin: 50
                    anchors.rightMargin: 50
                    color: Material.background 
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 20 
                        Button {
                            id: loadConfigButton
                            Layout.alignment: Qt.AlignCenter
                            text: qsTr("Load")
                            font.pixelSize: fontSizeLarge 
                            onClicked: {
                                configFileDialog.visible = true
                            }
                            enabled: loadButtonEnabled 
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: Material.background 
                            ScrollView {
                                id: configScrolView
                                anchors.fill: parent
                                TextArea {
                                    id: configTextArea
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    readOnly: false 
                                    font.pixelSize: fontSizeSmall
                                    text: configInfoText
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    FileDialog {
        id: configFileDialog
        title: qsTr("Please choose a file")
        onAccepted: {
            configFileDialog.visible = false
            backend.on_load_config_file(configFileDialog.selectedFile.toString())
        }
    }
    MessageDialog {
        id: errorMessageDialog
        text: errorMessageText
        visible: errorMessageVisible
        title: "Error"
    }
}

