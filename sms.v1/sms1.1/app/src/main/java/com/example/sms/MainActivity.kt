package com.example.myapplication

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.telephony.SmsManager
import android.telephony.SubscriptionInfo
import android.telephony.SubscriptionManager
import android.view.Menu
import android.view.MenuItem
import android.widget.Button
import android.widget.LinearLayout
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

class MainActivity : AppCompatActivity() {
    private lateinit var buttonsContainer: LinearLayout
    private var buttonConfigs = mutableListOf<ButtonConfig>()
    private val gson = Gson()
    private val smsPermissionCode = 100
    private lateinit var subscriptionManager: SubscriptionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        buttonsContainer = findViewById(R.id.buttonsContainer)
        subscriptionManager = getSystemService(SubscriptionManager::class.java)

        checkSmsPermission()
        loadButtonConfigs()
        createButtonsFromConfigs()
    }

    private fun checkSmsPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.SEND_SMS)
            != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.SEND_SMS),
                smsPermissionCode
            )
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == smsPermissionCode) {
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
                startActivityForResult(
                    Intent(this, ButtonManagementActivity::class.java),
                    REQUEST_CODE_CONFIG
                )
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_CODE_CONFIG && resultCode == RESULT_OK) {
            loadButtonConfigs()
            createButtonsFromConfigs()
        }
    }

    private fun loadButtonConfigs() {
        val sharedPref = getSharedPreferences("SMSAppPrefs", MODE_PRIVATE)
        val json = sharedPref.getString("buttonConfigs", "[]") ?: "[]"
        val type = object : TypeToken<List<ButtonConfig>>() {}.type
        buttonConfigs = gson.fromJson(json, type) ?: mutableListOf()
    }

    private fun createButtonsFromConfigs() {
        buttonsContainer.removeAllViews()
        buttonConfigs.forEach { config ->
            Button(this).apply {
                text = "${config.name} (SIM${config.simSlot + 1})"
                setOnClickListener { sendSms(config) }
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    bottomMargin = 16
                }
                buttonsContainer.addView(this)
            }
        }
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

    companion object {
        const val REQUEST_CODE_CONFIG = 1
    }
}