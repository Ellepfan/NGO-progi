package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.telephony.SubscriptionManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

class ButtonManagementActivity : AppCompatActivity() {
    private lateinit var buttonsContainer: LinearLayout
    private var buttonConfigs = mutableListOf<ButtonConfig>()
    private val gson = Gson()
    private lateinit var subscriptionManager: SubscriptionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_button_management)
        subscriptionManager = getSystemService(SubscriptionManager::class.java)

        buttonsContainer = findViewById(R.id.buttonsContainer)
        loadButtonConfigs()
        updateButtonsList()

        findViewById<Button>(R.id.addNewButton).setOnClickListener {
            startActivityForResult(
                Intent(this, ButtonConfigActivity::class.java),
                MainActivity.REQUEST_CODE_CONFIG
            )
        }
    }

    private fun loadButtonConfigs() {
        val sharedPref = getSharedPreferences("SMSAppPrefs", MODE_PRIVATE)
        val json = sharedPref.getString("buttonConfigs", "[]") ?: "[]"
        val type = object : TypeToken<List<ButtonConfig>>() {}.type
        buttonConfigs = gson.fromJson(json, type) ?: mutableListOf()
    }

    private fun updateButtonsList() {
        buttonsContainer.removeAllViews()

        if (buttonConfigs.isEmpty()) {
            val emptyText = Button(this).apply {
                text = "Нет сохраненных кнопок"
                isEnabled = false
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
            }
            buttonsContainer.addView(emptyText)
            return
        }

        buttonConfigs.forEachIndexed { index, config ->
            val buttonRow = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    bottomMargin = 16
                }
            }

            // Кнопка просмотра
            Button(this).apply {
                text = "${index + 1}. ${config.name} (SIM${config.simSlot + 1})"
                layoutParams = LinearLayout.LayoutParams(
                    0,
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    1f
                )
                setOnClickListener {
                    showButtonDetails(config)
                }
                buttonRow.addView(this)
            }

            // Кнопка редактирования
            Button(this).apply {
                text = "✏️"
                setOnClickListener {
                    editButton(config)
                }
                buttonRow.addView(this)
            }

            // Кнопка удаления
            Button(this).apply {
                text = "❌"
                setOnClickListener {
                    deleteButton(index)
                }
                buttonRow.addView(this)
            }

            buttonsContainer.addView(buttonRow)
        }
    }

    private fun showButtonDetails(config: ButtonConfig) {
        Toast.makeText(
            this,
            "Телефон: ${config.phoneNumber}\nСообщение: ${config.message}\nSIM: ${config.simSlot + 1}",
            Toast.LENGTH_LONG
        ).show()
    }

    private fun editButton(config: ButtonConfig) {
        startActivityForResult(
            Intent(this, ButtonConfigActivity::class.java).apply {
                putExtra("buttonId", config.id)
            },
            MainActivity.REQUEST_CODE_CONFIG
        )
    }

    private fun deleteButton(index: Int) {
        buttonConfigs.removeAt(index)
        saveButtonConfigs()
        updateButtonsList()
        Toast.makeText(this, "Кнопка удалена", Toast.LENGTH_SHORT).show()
    }

    private fun saveButtonConfigs() {
        try {
            val sharedPref = getSharedPreferences("SMSAppPrefs", MODE_PRIVATE)
            sharedPref.edit().apply {
                putString("buttonConfigs", gson.toJson(buttonConfigs))
                apply()
            }
        } catch (e: Exception) {
            Toast.makeText(this, "Ошибка сохранения: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == MainActivity.REQUEST_CODE_CONFIG && resultCode == RESULT_OK) {
            data?.let { handleConfigResult(it) }
        }
    }

    private fun handleConfigResult(data: Intent) {
        val id = data.getStringExtra("id") ?: return
        val name = data.getStringExtra("name") ?: return
        val phoneNumber = data.getStringExtra("phoneNumber") ?: return
        val message = data.getStringExtra("message") ?: return
        val simSlot = data.getIntExtra("simSlot", 0)

        val existingIndex = buttonConfigs.indexOfFirst { it.id == id }
        if (existingIndex != -1) {
            buttonConfigs[existingIndex] = ButtonConfig(id, name, message, phoneNumber, simSlot)
        } else {
            buttonConfigs.add(ButtonConfig(id, name, message, phoneNumber, simSlot))
        }

        saveButtonConfigs()
        updateButtonsList()
    }
}