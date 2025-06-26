package com.example.myapplication

data class ButtonConfig(
    val objectName: String, // Новое поле для названия объекта
    val id: String,
    val name: String,
    val message: String,
    val phoneNumber: String,
    val simSlot: Int = 0
) {
    override fun toString(): String {
        return "ButtonConfig(id='$id', name='$name', phoneNumber='$phoneNumber', simSlot=$simSlot)"
    }
}