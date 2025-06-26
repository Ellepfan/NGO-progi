package com.example.relecontrol

import android.app.AlertDialog
import android.content.Context
import android.content.SharedPreferences
import android.net.ConnectivityManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.LayoutInflater
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import okhttp3.*
import org.json.JSONObject
import java.io.IOException

class MainActivity : AppCompatActivity() {
    private val client = OkHttpClient()
    private val handler = Handler(Looper.getMainLooper())
    private var baseUrl = "http://192.168.43.243/switch/"
    private lateinit var sharedPrefs: SharedPreferences

    private lateinit var relays: List<Switch>
    private lateinit var switchAll: Switch
    private val relayIds = listOf("relay1", "relay2", "relay3", "relay4",
        "relay5", "relay6", "relay7", "relay8")

    // Храним слушатели для каждого реле
    private val relayListeners = mutableListOf<CompoundButton.OnCheckedChangeListener>()

    private val statusUpdater = object : Runnable {
        override fun run() {
            fetchRelaysStatus()
            handler.postDelayed(this, 1000)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        try {
            if (!isNetworkAvailable()) {
                showErrorAndFinish("Нет интернет-соединения")
                return
            }

            sharedPrefs = getSharedPreferences("RelaySettings", MODE_PRIVATE)

            switchAll = findViewById(R.id.switchAll)
            relays = listOf(
                findViewById(R.id.Rele1),
                findViewById(R.id.Rele2),
                findViewById(R.id.Rele3),
                findViewById(R.id.Rele4),
                findViewById(R.id.Rele5),
                findViewById(R.id.Rele6),
                findViewById(R.id.Rele7),
                findViewById(R.id.Rele8)
            )

            if (relays.any { it == null }) {
                throw IllegalStateException("Не все Switch элементы найдены")
            }

            setupRelays()
            setupAllSwitch()
            loadSettings()

            findViewById<Button>(R.id.settings_button)?.setOnClickListener {
                showSettingsDialog()
            }

            handler.post(statusUpdater)

        } catch (e: Exception) {
            Log.e("MainActivity", "Ошибка инициализации", e)
            showErrorAndFinish("Ошибка запуска: ${e.localizedMessage}")
        }
    }

    private fun setupRelays() {
        relays.forEachIndexed { index, switch ->
            val listener = CompoundButton.OnCheckedChangeListener { buttonView, isChecked ->
                if (buttonView.isPressed) { // Проверяем, что изменение вызвано пользователем
                    try {
                        val relayId = relayIds.getOrNull(index) ?: return@OnCheckedChangeListener
                        val url = if (isChecked) "$baseUrl$relayId/turn_on" else "$baseUrl$relayId/turn_off"
                        sendGetRequest(url)
                        updateAllSwitchState()
                    } catch (e: Exception) {
                        Log.e("Relay", "Ошибка изменения состояния", e)
                    }
                }
            }
            relayListeners.add(listener)
            switch.setOnCheckedChangeListener(listener)
        }
    }

    private fun setupAllSwitch() {
        switchAll.setOnCheckedChangeListener { _, isChecked ->
            if (switchAll.isPressed) {
                relays.forEachIndexed { index, switch ->
                    switch.setOnCheckedChangeListener(null)
                    switch.isChecked = isChecked
                    switch.setOnCheckedChangeListener(relayListeners[index])

                    val relayId = relayIds.getOrNull(index) ?: return@forEachIndexed
                    val url = if (isChecked) "$baseUrl$relayId/turn_on" else "$baseUrl$relayId/turn_off"
                    sendGetRequest(url)
                }
            }
        }
    }

    private fun updateAllSwitchState() {
        val anyRelayOn = relays.any { it.isChecked }
        handler.post {
            switchAll.setOnCheckedChangeListener(null)
            switchAll.isChecked = anyRelayOn
            switchAll.setOnCheckedChangeListener { _, isChecked ->
                if (switchAll.isPressed) {
                    relays.forEachIndexed { index, switch ->
                        switch.setOnCheckedChangeListener(null)
                        switch.isChecked = isChecked
                        switch.setOnCheckedChangeListener(relayListeners[index])

                        val relayId = relayIds.getOrNull(index) ?: return@forEachIndexed
                        val url = if (isChecked) "$baseUrl$relayId/turn_on" else "$baseUrl$relayId/turn_off"
                        sendGetRequest(url)
                    }
                }
            }
        }
    }

    private fun isNetworkAvailable(): Boolean {
        return try {
            val connectivityManager = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val networkInfo = connectivityManager.activeNetworkInfo
            networkInfo?.isConnected ?: false
        } catch (e: Exception) {
            false
        }
    }

    private fun showErrorAndFinish(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
        finish()
    }

    private fun loadSettings() {
        try {
            baseUrl = "http://${sharedPrefs.getString("ip_address", "192.168.43.243")}/switch/"

            for (i in 1..8) {
                val textViewId = resources.getIdentifier("custom_name$i", "id", packageName)
                val relayName = sharedPrefs.getString("relay${i}_name", "Имя $i")
                findViewById<TextView>(textViewId)?.text = relayName
            }
        } catch (e: Exception) {
            Log.e("Settings", "Ошибка загрузки настроек", e)
        }
    }

    private fun showSettingsDialog() {
        try {
            val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_settings, null)
            val dialog = AlertDialog.Builder(this)
                .setView(dialogView)
                .setTitle("Настройки реле")
                .create()

            val ipInput = dialogView.findViewById<EditText>(R.id.ip_address_input)
            ipInput?.setText(baseUrl.removePrefix("http://").removeSuffix("/switch/"))

            for (i in 1..8) {
                val editTextId = resources.getIdentifier("rele${i}_name", "id", packageName)
                val textViewId = resources.getIdentifier("custom_name$i", "id", packageName)
                dialogView.findViewById<EditText>(editTextId)?.setText(
                    findViewById<TextView>(textViewId)?.text
                )
            }

            dialogView.findViewById<Button>(R.id.save_button)?.setOnClickListener {
                try {
                    val newIp = ipInput?.text?.toString() ?: ""
                    if (newIp.isNotBlank()) {
                        baseUrl = "http://$newIp/switch/"
                        sharedPrefs.edit().putString("ip_address", newIp).apply()
                    }

                    for (i in 1..8) {
                        val editTextId = resources.getIdentifier("rele${i}_name", "id", packageName)
                        val textViewId = resources.getIdentifier("custom_name$i", "id", packageName)
                        val newName = dialogView.findViewById<EditText>(editTextId)?.text?.toString()
                        if (!newName.isNullOrBlank()) {
                            findViewById<TextView>(textViewId)?.text = newName
                            sharedPrefs.edit().putString("relay${i}_name", newName).apply()
                        }
                    }

                    Toast.makeText(this, "Настройки сохранены", Toast.LENGTH_SHORT).show()
                    dialog.dismiss()
                } catch (e: Exception) {
                    Log.e("Settings", "Ошибка сохранения", e)
                }
            }

            dialog.show()
        } catch (e: Exception) {
            Log.e("Dialog", "Ошибка отображения диалога", e)
        }
    }

    private fun fetchRelaysStatus() {
        try {
            relayIds.forEachIndexed { index, relayId ->
                val url = "$baseUrl$relayId"
                if (url.isBlank()) {
                    Log.e("Network", "Пустой URL для реле $relayId")
                    return@forEachIndexed
                }

                val request = Request.Builder()
                    .url(url)
                    .build()

                client.newCall(request).enqueue(object : Callback {
                    override fun onFailure(call: Call, e: IOException) {
                        Log.e("Network", "Ошибка запроса к $url", e)
                    }

                    override fun onResponse(call: Call, response: Response) {
                        try {
                            response.use {
                                if (!response.isSuccessful) {
                                    Log.e("Network", "Неуспешный ответ: ${response.code}")
                                    return
                                }

                                val body = response.body?.string() ?: run {
                                    Log.e("Network", "Пустое тело ответа")
                                    return
                                }

                                try {
                                    val json = JSONObject(body)
                                    val state = json.getString("state")

                                    runOnUiThread {
                                        try {
                                            relays.getOrNull(index)?.let { switch ->
                                                switch.setOnCheckedChangeListener(null)
                                                switch.isChecked = state == "ON"
                                                switch.setOnCheckedChangeListener(relayListeners[index])
                                            }
                                            updateAllSwitchState()
                                        } catch (e: Exception) {
                                            Log.e("UI", "Ошибка обновления UI", e)
                                        }
                                    }
                                } catch (e: Exception) {
                                    Log.e("JSON", "Ошибка парсинга ответа", e)
                                }
                            }
                        } catch (e: Exception) {
                            Log.e("Response", "Ошибка обработки ответа", e)
                        }
                    }
                })
            }
        } catch (e: Exception) {
            Log.e("Fetch", "Ошибка получения статуса", e)
        }
    }

    private fun sendGetRequest(url: String) {
        try {
            Log.d("Network", "Отправка запроса: $url")
            if (url.isBlank()) {
                Log.e("Network", "Пустой URL запроса")
                return
            }

            val request = Request.Builder()
                .url(url)
                .build()

            client.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    Log.e("Network", "Ошибка запроса к $url", e)
                }

                override fun onResponse(call: Call, response: Response) {
                    try {
                        response.use {
                            if (!response.isSuccessful) {
                                Log.e("Network", "Неуспешный ответ: ${response.code}")
                            } else {
                                Log.d("Network", "Успешный ответ от $url")
                            }
                        }
                    } catch (e: Exception) {
                        Log.e("Response", "Ошибка обработки ответа", e)
                    }
                }
            })
        } catch (e: Exception) {
            Log.e("Request", "Ошибка отправки запроса", e)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            handler.removeCallbacks(statusUpdater)
        } catch (e: Exception) {
            Log.e("Lifecycle", "Ошибка в onDestroy", e)
        }
    }
}