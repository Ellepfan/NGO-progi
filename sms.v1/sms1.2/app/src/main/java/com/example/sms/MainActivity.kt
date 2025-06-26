package com.example.myapplication

import android.Manifest
import android.app.AlertDialog
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.telephony.SmsManager
import android.telephony.SubscriptionManager
import android.util.TypedValue
import android.view.Menu
import android.view.MenuItem
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

class MainActivity : AppCompatActivity() {
    private lateinit var buttonsContainer: LinearLayout
    private val objectButtonsMap = mutableMapOf<String, MutableList<ButtonConfig>>()
    private val gson = Gson()
    private lateinit var subscriptionManager: SubscriptionManager

    private val configActivityResult = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            loadButtonConfigs()
            createObjectButtons()
            Toast.makeText(this, "Изменения сохранены", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        buttonsContainer = findViewById(R.id.buttonsContainer)
        subscriptionManager = getSystemService(SubscriptionManager::class.java)

        checkSmsPermission()
        loadButtonConfigs()
        createObjectButtons()
    }

    private fun checkSmsPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.SEND_SMS)
            != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.SEND_SMS),
                Constants.SMS_PERMISSION_CODE
            )
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == Constants.SMS_PERMISSION_CODE) {
            if (grantResults.isEmpty() || grantResults[0] != PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Без разрешения отправка SMS невозможна", Toast.LENGTH_LONG).show()
            }
        }
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.main_menu, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.menu_manage_buttons -> {
                configActivityResult.launch(Intent(this, ButtonManagementActivity::class.java))
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    private fun loadButtonConfigs() {
        val sharedPref = getSharedPreferences("SMSAppPrefs", MODE_PRIVATE)
        val json = sharedPref.getString("buttonConfigs", "[]") ?: "[]"
        val type = object : TypeToken<List<ButtonConfig>>() {}.type
        val configs = gson.fromJson<List<ButtonConfig>>(json, type) ?: listOf()

        objectButtonsMap.clear()
        configs.forEach { config ->
            objectButtonsMap.getOrPut(config.objectName) { mutableListOf() }.add(config)
        }
    }

    private fun createObjectButtons() {
        buttonsContainer.removeAllViews()

        if (objectButtonsMap.isEmpty()) {
            val emptyText = TextView(this).apply {
                text = "Нет сохраненных объектов"
                setPadding(0, 16.dpToPx(), 0, 0)
            }
            buttonsContainer.addView(emptyText)
            return
        }

        objectButtonsMap.keys.forEach { objectName ->
            Button(this).apply {
                text = objectName
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply { bottomMargin = 16.dpToPx() }

                setOnClickListener {
                    showButtonsForObject(objectName)
                }
                buttonsContainer.addView(this)
            }
        }
    }

    private fun showButtonsForObject(objectName: String) {
        val buttons = objectButtonsMap[objectName] ?: return

        AlertDialog.Builder(this)
            .setTitle("Кнопки объекта: $objectName")
            .setItems(buttons.map { "${it.name} (SIM${it.simSlot + 1})" }.toTypedArray()) { _, which ->
                sendSms(buttons[which])
            }
            .setNegativeButton("Назад", null)
            .show()
    }

    private fun sendSms(config: ButtonConfig) {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.SEND_SMS)
            != PackageManager.PERMISSION_GRANTED) {
            checkSmsPermission()
            return
        }

        try {
            val subscriptions = subscriptionManager.activeSubscriptionInfoList
            if (subscriptions.size > config.simSlot) {
                val subId = subscriptions[config.simSlot].subscriptionId
                SmsManager.getSmsManagerForSubscriptionId(subId)
                    .sendTextMessage(config.phoneNumber, null, config.message, null, null)
                Toast.makeText(this, "SMS отправлено с SIM${config.simSlot + 1} на ${config.phoneNumber}", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "Выбранная SIM-карта не доступна", Toast.LENGTH_LONG).show()
            }
        } catch (e: Exception) {
            Toast.makeText(this, "Ошибка: ${e.localizedMessage}", Toast.LENGTH_LONG).show()
        }
    }

    private fun Int.dpToPx(): Int = TypedValue.applyDimension(
        TypedValue.COMPLEX_UNIT_DIP,
        this.toFloat(),
        resources.displayMetrics
    ).toInt()
}