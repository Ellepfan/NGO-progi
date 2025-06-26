package com.example.relecontrol

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Switch
import androidx.appcompat.app.AppCompatActivity
import okhttp3.*
import org.json.JSONObject
import java.io.IOException

class MainActivity : AppCompatActivity() {
    private val client = OkHttpClient()
    private val handler = Handler(Looper.getMainLooper())
    private val baseUrl = "http://192.168.43.243/switch/"

    // Список всех реле
    private lateinit var relays: List<Switch>
    private val relayIds = listOf("relay1", "relay2", "relay3", "relay4",
        "relay5", "relay6", "relay7", "relay8")

    // Runnable для периодического обновления
    private val statusUpdater = object : Runnable {
        override fun run() {
            fetchRelaysStatus()
            handler.postDelayed(this, 1000) // Повтор каждую секунду
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Инициализация всех переключателей
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

        // Установка слушателей для каждого реле
        relays.forEachIndexed { index, switch ->
            switch.setOnCheckedChangeListener { _, isChecked ->
                val relayId = relayIds[index]
                val url = if (isChecked) {
                    "$baseUrl$relayId/turn_on"
                } else {
                    "$baseUrl$relayId/turn_off"
                }
                sendGetRequest(url)
            }
        }

        // Начинаем обновление статуса
        handler.post(statusUpdater)
    }

    override fun onDestroy() {
        super.onDestroy()
        // Останавливаем обновление при уничтожении Activity
        handler.removeCallbacks(statusUpdater)
    }

    private fun fetchRelaysStatus() {
        relayIds.forEachIndexed { index, relayId ->
            val request = Request.Builder()
                .url("$baseUrl$relayId")
                .get()
                .build()

            client.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    e.printStackTrace()
                }

                override fun onResponse(call: Call, response: Response) {
                    response.body?.use { responseBody ->
                        try {
                            val json = JSONObject(responseBody.string())
                            val state = json.getString("state") // "ON" или "OFF"

                            runOnUiThread {
                                // Обновляем Switch без вызова слушателя
                                relays[index].setOnCheckedChangeListener(null)
                                relays[index].isChecked = state == "ON"
                                relays[index].setOnCheckedChangeListener { _, isChecked ->
                                    val url = if (isChecked) {
                                        "$baseUrl$relayId/turn_on"
                                    } else {
                                        "$baseUrl$relayId/turn_off"
                                    }
                                    sendGetRequest(url)
                                }
                            }
                        } catch (e: Exception) {
                            e.printStackTrace()
                        }
                    }
                }
            })
        }
    }

    private fun sendGetRequest(url: String) {
        val request = Request.Builder()
            .url(url)
            .get()
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                e.printStackTrace()
            }

            override fun onResponse(call: Call, response: Response) {
                println("Response for $url: ${response.code}")
            }
        })
    }
}