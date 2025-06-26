package com.example.myapplication

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.telephony.SubscriptionManager
import android.widget.Button
import android.widget.EditText
import android.widget.RadioButton
import android.widget.RadioGroup
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import java.util.UUID

class ButtonConfigActivity : AppCompatActivity() {
    private lateinit var nameEditText: EditText
    private lateinit var phoneEditText: EditText
    private lateinit var messageEditText: EditText
    private lateinit var simRadioGroup: RadioGroup
    private var buttonId: String? = null
    private val gson = Gson()
    private lateinit var subscriptionManager: SubscriptionManager
    private val permissionRequestCode = 1001

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_button_config)

        checkPermissions()
        initViews()
        loadButtonConfigIfExists()
    }

    private fun checkPermissions() {
        subscriptionManager = getSystemService(SubscriptionManager::class.java)
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_PHONE_STATE)
            != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.READ_PHONE_STATE),
                permissionRequestCode
            )
        } else {
            setupSimOptions()
        }
    }

    private fun initViews() {
        nameEditText = findViewById(R.id.nameEditText)
        phoneEditText = findViewById(R.id.phoneEditText)
        messageEditText = findViewById(R.id.messageEditText)
        simRadioGroup = findViewById(R.id.simRadioGroup)

        findViewById<Button>(R.id.saveButton).setOnClickListener {
            saveButtonConfig()
        }
    }

    private fun loadButtonConfigIfExists() {
        buttonId = intent.getStringExtra("buttonId")
        buttonId?.let { loadButtonConfig() }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == permissionRequestCode && grantResults.isNotEmpty() &&
            grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            setupSimOptions()
        } else {
            Toast.makeText(this, "Для работы с SIM-картами нужно разрешение", Toast.LENGTH_LONG).show()
        }
    }

    private fun setupSimOptions() {
        try {
            val subscriptions = subscriptionManager.activeSubscriptionInfoList
            findViewById<RadioButton>(R.id.sim1Radio).apply {
                isEnabled = subscriptions.isNotEmpty()
                text = if (subscriptions.isNotEmpty()) "SIM1: ${subscriptions[0].displayName}" else "SIM1: Недоступно"
            }
            findViewById<RadioButton>(R.id.sim2Radio).apply {
                isEnabled = subscriptions.size > 1
                text = if (subscriptions.size > 1) "SIM2: ${subscriptions[1].displayName}" else "SIM2: Недоступно"
            }
        } catch (e: Exception) {
            Toast.makeText(this, "Ошибка доступа к SIM-картам", Toast.LENGTH_SHORT).show()
        }
    }

    private fun loadButtonConfig() {
        val sharedPref = getSharedPreferences("SMSAppPrefs", MODE_PRIVATE)
        val json = sharedPref.getString("buttonConfigs", "[]") ?: "[]"
        val type = object : TypeToken<List<ButtonConfig>>() {}.type
        val configs = gson.fromJson<List<ButtonConfig>>(json, type) ?: listOf()

        configs.find { it.id == buttonId }?.let { config ->
            nameEditText.setText(config.name)
            phoneEditText.setText(config.phoneNumber)
            messageEditText.setText(config.message)
            simRadioGroup.check(
                when (config.simSlot) {
                    0 -> R.id.sim1Radio
                    1 -> R.id.sim2Radio
                    else -> R.id.sim1Radio
                }
            )
        }
    }

    private fun saveButtonConfig() {
        val name = nameEditText.text.toString().trim()
        val phone = phoneEditText.text.toString().trim()
        val message = messageEditText.text.toString().trim()

        if (name.isEmpty() || phone.isEmpty() || message.isEmpty()) {
            Toast.makeText(this, "Заполните все поля", Toast.LENGTH_SHORT).show()
            return
        }

        val simSlot = when (simRadioGroup.checkedRadioButtonId) {
            R.id.sim1Radio -> 0
            R.id.sim2Radio -> 1
            else -> 0
        }

        setResult(RESULT_OK, Intent().apply {
            putExtra("id", buttonId ?: UUID.randomUUID().toString())
            putExtra("name", name)
            putExtra("phoneNumber", phone)
            putExtra("message", message)
            putExtra("simSlot", simSlot)
        })
        finish()
    }
}