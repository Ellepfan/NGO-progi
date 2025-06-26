package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.telephony.SubscriptionManager
import android.util.TypedValue
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

class ButtonManagementActivity : AppCompatActivity() {
    private lateinit var buttonsContainer: LinearLayout
    private var buttonConfigs = mutableListOf<ButtonConfig>()
    private val gson = Gson()
    private lateinit var subscriptionManager: SubscriptionManager
    private val objectButtonsMap = mutableMapOf<String, MutableList<ButtonConfig>>()

    private val configActivityResult = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            loadButtonConfigs()
            updateButtonsList()
            Toast.makeText(this, "Изменения сохранены", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_button_management)
        subscriptionManager = getSystemService(SubscriptionManager::class.java)

        buttonsContainer = findViewById(R.id.buttonsContainer)
        loadButtonConfigs()
        updateButtonsList()

        findViewById<Button>(R.id.addNewButton).setOnClickListener {
            configActivityResult.launch(Intent(this, ButtonConfigActivity::class.java))
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

        objectButtonsMap.clear()
        buttonConfigs.forEach { config ->
            objectButtonsMap.getOrPut(config.objectName) { mutableListOf() }.add(config)
        }

        if (objectButtonsMap.isEmpty()) {
            val emptyText = TextView(this).apply {
                text = "Нет сохраненных кнопок"
                setPadding(0, 16.dpToPx(), 0, 0)
            }
            buttonsContainer.addView(emptyText)
            return
        }

        objectButtonsMap.keys.forEach { objectName ->
            val objectLayout = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply { bottomMargin = 24.dpToPx() }
            }

            TextView(this).apply {
                text = objectName
                textSize = 18f
                setPadding(0, 16.dpToPx(), 0, 8.dpToPx())
                objectLayout.addView(this)
            }

            objectButtonsMap[objectName]?.forEachIndexed { index, config ->
                val buttonRow = LinearLayout(this).apply {
                    orientation = LinearLayout.HORIZONTAL
                    layoutParams = LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT
                    ).apply { bottomMargin = 8.dpToPx() }
                }

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

                Button(this).apply {
                    text = "✏️"
                    setOnClickListener {
                        editButton(config)
                    }
                    buttonRow.addView(this)
                }

                Button(this).apply {
                    text = "❌"
                    setOnClickListener {
                        deleteButton(config)
                    }
                    buttonRow.addView(this)
                }

                objectLayout.addView(buttonRow)
            }

            buttonsContainer.addView(objectLayout)
        }
    }

    private fun showButtonDetails(config: ButtonConfig) {
        Toast.makeText(
            this,
            "Объект: ${config.objectName}\nТелефон: ${config.phoneNumber}\nСообщение: ${config.message}\nSIM: ${config.simSlot + 1}",
            Toast.LENGTH_LONG
        ).show()
    }

    private fun editButton(config: ButtonConfig) {
        configActivityResult.launch(
            Intent(this, ButtonConfigActivity::class.java).apply {
                putExtra("buttonId", config.id)
            }
        )
    }

    private fun deleteButton(config: ButtonConfig) {
        buttonConfigs.removeAll { it.id == config.id }
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

    private fun Int.dpToPx(): Int = TypedValue.applyDimension(
        TypedValue.COMPLEX_UNIT_DIP,
        this.toFloat(),
        resources.displayMetrics
    ).toInt()
}