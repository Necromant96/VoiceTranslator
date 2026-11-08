package com.example.voicetranslator

import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.view.LayoutInflater
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.BaseAdapter
import android.widget.Button
import android.widget.CheckBox
import android.widget.FrameLayout
import android.widget.ListView
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.Locale
import kotlin.concurrent.thread

class MainActivity : Activity() {

    companion object {
        /** Все поддерживаемые языки: код -> название. */
        val LANGS = listOf(
            "ru" to "Русский 🇷🇺",
            "en" to "English 🇬🇧",
            "de" to "Deutsch 🇩🇪",
            "fr" to "Français 🇫🇷",
            "es" to "Español 🇪🇸",
            "it" to "Italiano 🇮🇹",
            "pt" to "Português 🇵🇹",
            "zh-CN" to "中文 🇨🇳",
            "ja" to "日本語 🇯🇵",
            "ko" to "한국어 🇰🇷",
            "tr" to "Türkçe 🇹🇷",
            "uk" to "Українська 🇺🇦",
            "pl" to "Polski 🇵🇱",
            "ar" to "العربية 🇸🇦",
            "hi" to "हिन्दी 🇮🇳"
        )
        private const val PERM_REQ = 101
    }

    /** Одна реплика диалога. speaker: 0 = A, 1 = B. */
    private class Msg(val speaker: Int, val original: String, val translated: String)

    private val messages = ArrayList<Msg>()
    private val ui = Handler(Looper.getMainLooper())

    private lateinit var recognizer: SpeechRecognizer
    private var tts: TextToSpeech? = null
    private var ttsReady = false
    private var lastSpokenSide = 0

    /** Сейчас слушает сторона: -1 никто, 0 = A, 1 = B. */
    private var listeningSide = -1
    /** Право на перезапуск распознавания после ошибки/результата. */
    private var wantRestart = false

    private lateinit var adapter: MsgAdapter
    private lateinit var spinA: Spinner
    private lateinit var spinB: Spinner
    private lateinit var tvStatus: TextView
    private lateinit var btnMicA: Button
    private lateinit var btnMicB: Button
    private lateinit var chkA: CheckBox
    private lateinit var chkB: CheckBox
    private lateinit var btnSwap: Button
    private lateinit var btnCopy: Button
    private lateinit var btnClear: Button
    private lateinit var listHistory: ListView

    /** Коды языков сторон A и B. */
    private var langA = "ru"
    private var langB = "en"

    // ---------- Жизненный цикл ----------

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        spinA = findViewById(R.id.spinA)
        spinB = findViewById(R.id.spinB)
        tvStatus = findViewById(R.id.tvStatus)
        btnMicA = findViewById(R.id.btnMicA)
        btnMicB = findViewById(R.id.btnMicB)
        chkA = findViewById(R.id.chkContinuousA)
        chkB = findViewById(R.id.chkContinuousB)
        btnSwap = findViewById(R.id.btnSwap)
        btnCopy = findViewById(R.id.btnCopy)
        btnClear = findViewById(R.id.btnClear)
        listHistory = findViewById(R.id.listHistory)

        val names = LANGS.map { it.second }
        val spinAdapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, names)
        spinAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        spinA.adapter = spinAdapter
        spinB.adapter = spinAdapter
        spinA.setSelection(0) // Русский
        spinB.setSelection(1) // English

        spinA.onItemSelectedListener = SideSpinner(0)
        spinB.onItemSelectedListener = SideSpinner(1)

        adapter = MsgAdapter()
        listHistory.adapter = adapter
        listHistory.transcriptMode = ListView.TRANSCRIPT_MODE_ALWAYS_SCROLL
        listHistory.setStackFromBottom(true)

        btnMicA.setOnClickListener { onMicClicked(0) }
        btnMicB.setOnClickListener { onMicClicked(1) }
        btnSwap.setOnClickListener { swapLanguages() }
        btnCopy.setOnClickListener { copyDialog() }
        btnClear.setOnClickListener {
            messages.clear()
            adapter.notifyDataSetChanged()
        }

        chkA.setOnCheckedChangeListener { _, checked ->
            if (checked) {
                chkB.isChecked = false
                startListening(0)
            } else if (listeningSide == 0 && !chkA.isChecked) {
                stopListening()
            }
        }
        chkB.setOnCheckedChangeListener { _, checked ->
            if (checked) {
                chkA.isChecked = false
                startListening(1)
            } else if (listeningSide == 1 && !chkB.isChecked) {
                stopListening()
            }
        }

        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            Toast.makeText(this, R.string.no_speech, Toast.LENGTH_LONG).show()
            btnMicA.isEnabled = false
            btnMicB.isEnabled = false
            chkA.isEnabled = false
            chkB.isEnabled = false
        }

        recognizer = SpeechRecognizer.createSpeechRecognizer(this)
        recognizer.setRecognitionListener(Listener())

        initTts()
    }

    override fun onDestroy() {
        wantRestart = false
        listeningSide = -1
        try { recognizer.destroy() } catch (_: Exception) {}
        tts?.stop()
        tts?.shutdown()
        super.onDestroy()
    }

    override fun onPause() {
        super.onPause()
        // При уходе с экрана — не оставляем «висящий» микрофон и TTS.
        stopListening()
        tts?.stop()
    }

    // ---------- Распознавание речи ----------

    private fun onMicClicked(side: Int) {
        val chk = if (side == 0) chkA else chkB
        if (chk.isChecked) {
            chk.isChecked = false // => stopListening()
            return
        }
        if (listeningSide == side) {
            stopListening()
            return
        }
        if (listeningSide != -1) stopListening()
        startListening(side)
    }

    private fun startListening(side: Int) {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) return
        if (checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(android.Manifest.permission.RECORD_AUDIO), PERM_REQ)
            // Снимем галочку до получения разрешения.
            if (side == 0) chkA.isChecked = false else chkB.isChecked = false
            return
        }
        listeningSide = side
        wantRestart = (side == 0 && chkA.isChecked) || (side == 1 && chkB.isChecked)
        setStatus(getString(R.string.hint_listening) + " → " + (if (side == 0) langA else langB))
        setMicUi(side)
        recognizer.cancel()

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, if (side == 0) langA else langB)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        }
        runCatching { recognizer.startListening(intent) }
            .onFailure { listeningSide = -1; setStatus(getString(R.string.hint_idle)) }
    }

    private fun stopListening() {
        wantRestart = false
        listeningSide = -1
        runCatching { recognizer.cancel() }
        setMicUi(-1)
        setStatus(getString(R.string.hint_idle))
    }

    /** Перезапускает распознавание той же стороны, если включён непрерывный режим. */
    private fun restartIfContinuous(side: Int) {
        if (!wantRestart || side < 0) return
        ui.postDelayed({
            if (wantRestart && listeningSide == -1 &&
                ((side == 0 && chkA.isChecked) || (side == 1 && chkB.isChecked))
            ) startListening(side)
        }, 350)
    }

    private inner class Listener : RecognitionListener {
        override fun onReadyForSpeech(params: Bundle?) {
            setStatus(getString(R.string.hint_listening))
        }

        override fun onBeginningOfSpeech() {}

        override fun onRmsChanged(rmsdB: Float) {}

        override fun onBufferReceived(buffer: ByteArray?) {}

        override fun onEndOfSpeech() {
            setStatus(getString(R.string.hint_processing))
        }

        override fun onError(error: Int) {
            val side = listeningSide
            listeningSide = -1
            val retryDelay = when (error) {
                SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> 1200L
                SpeechRecognizer.ERROR_SPEECH_TIMEOUT,
                SpeechRecognizer.ERROR_NO_MATCH -> 250L
                else -> 800L
            }
            if (wantRestart && side >= 0) {
                ui.postDelayed({
                    if (wantRestart && listeningSide == -1 &&
                        ((side == 0 && chkA.isChecked) || (side == 1 && chkB.isChecked))
                    ) startListening(side)
                }, retryDelay)
            } else {
                setMicUi(-1)
                setStatus(getString(R.string.hint_idle))
            }
        }

        override fun onPartialResults(partialResults: Bundle?) {
            val text = partialResults
                ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull() ?: return
            if (text.isNotBlank()) setStatus("«$text»")
        }

        override fun onEvent(eventType: Int, params: Bundle?) {}

        override fun onResults(results: Bundle?) {
            val side = listeningSide
            listeningSide = -1
            val text = results
                ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull()?.trim()

            if (text.isNullOrEmpty()) {
                if (wantRestart && side >= 0) setMicUi(side)
                restartIfContinuous(side)
                setStatus(getString(R.string.hint_idle))
                return
            }
            setMicUi(-1)
            handleRecognized(side, text)
        }
    }

    private fun handleRecognized(side: Int, text: String) {
        val src = if (side == 0) langA else langB
        val tgt = if (side == 0) langB else langA
        setStatus(getString(R.string.hint_translating))
        translate(text, src, tgt) { translated ->
            messages.add(Msg(side, text, translated))
            adapter.notifyDataSetChanged()
            speak(translated, tgt, side)
        }
    }

    // ---------- Перевод ----------

    /**
     * Переводит текст и вызывает [cb] в UI-потоке.
     * Основной сервис — Google Translate (gtx, без ключа), резерв — MyMemory.
     */
    private fun translate(text: String, from: String, to: String, cb: (String) -> Unit) {
        thread {
            var result: String? = null
            try {
                val url = "https://translate.googleapis.com/translate_a/single" +
                        "?client=gtx&sl=" + URLEncoder.encode(from, "UTF-8") +
                        "&tl=" + URLEncoder.encode(to, "UTF-8") +
                        "&dt=t&q=" + URLEncoder.encode(text, "UTF-8")
                val response = httpGet(url)
                if (response != null) {
                    val arr = JSONArray(response)
                    val parts = arr.getJSONArray(0)
                    val sb = StringBuilder()
                    for (i in 0 until parts.length()) {
                        sb.append(parts.getJSONArray(i).getString(0))
                    }
                    if (sb.isNotBlank()) result = sb.toString().trim()
                }
            } catch (_: Exception) {
            }

            // Резервный переводчик
            if (result == null) {
                try {
                    val url = "https://api.mymemory.translated.net/get" +
                            "?q=" + URLEncoder.encode(text, "UTF-8") +
                            "&langpair=" + URLEncoder.encode("$from|$to", "UTF-8")
                    val response = httpGet(url)
                    if (response != null) {
                        val translated = JSONObject(response)
                            .getJSONObject("responseData")
                            .optString("translatedText", "")
                        if (translated.isNotBlank() &&
                            !translated.contains("MYMEMORY WARNING", ignoreCase = true)
                        ) result = translated.trim()
                    }
                } catch (_: Exception) {
                }
            }

            val final = result ?: run {
                runOnUiThread {
                    Toast.makeText(this, R.string.translation_error, Toast.LENGTH_SHORT).show()
                    restartIfContinuous(side = lastSpokenSide)
                }
                return@thread
            }
            runOnUiThread { cb(final) }
        }
    }

    private fun httpGet(url: String): String? {
        var conn: HttpURLConnection? = null
        return try {
            conn = (URL(url).openConnection() as HttpURLConnection).apply {
                connectTimeout = 8000
                readTimeout = 8000
                requestMethod = "GET"
                setRequestProperty("User-Agent", "Mozilla/5.0 (Android) VoiceTranslator/1.0")
            }
            val code = conn.responseCode
            val stream = if (code in 200..299) conn.inputStream else conn.errorStream
            stream?.bufferedReader()?.use { it.readText() }
        } catch (_: Exception) {
            null
        } finally {
            conn?.disconnect()
        }
    }

    // ---------- Синтез речи (TTS) ----------

    private fun initTts() {
        tts = TextToSpeech(this) { status ->
            ttsReady = status == TextToSpeech.SUCCESS
        }
        tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) {
                runOnUiThread { setStatus(getString(R.string.hint_speaking)) }
            }

            override fun onDone(utteranceId: String?) {
                runOnUiThread {
                    setStatus(getString(R.string.hint_idle))
                    restartIfContinuous(lastSpokenSide)
                }
            }

            @Deprecated("Deprecated in Java")
            override fun onError(utteranceId: String?) {
                runOnUiThread { setStatus(getString(R.string.hint_idle)) }
            }
        })
    }

    private fun speak(text: String, langCode: String, side: Int) {
        val engine = tts
        if (engine == null || !ttsReady) return
        val loc = langToLocale(langCode)
        val set = engine.setLanguage(loc)
        if (set == TextToSpeech.LANG_MISSING_DATA || set == TextToSpeech.LANG_NOT_SUPPORTED) {
            Toast.makeText(this, R.string.tts_lang_error, Toast.LENGTH_SHORT).show()
            setStatus(getString(R.string.hint_idle))
            restartIfContinuous(side)
            return
        }
        lastSpokenSide = side
        engine.stop()
        engine.speak(text, TextToSpeech.QUEUE_FLUSH, null, "msg_${messages.size}")
    }

    private fun langToLocale(code: String): Locale = try {
        Locale.forLanguageTag(code)
    } catch (_: Exception) {
        Locale.getDefault()
    }

    // ---------- Вспомогательное ----------

    private fun setStatus(text: String) = runOnUiThread { tvStatus.text = text }

    /** Переключает внешний вид кнопок микрофона: активная сторона — красная «⏹». */
    private fun setMicUi(side: Int) = runOnUiThread {
        when (side) {
            0 -> {
                btnMicA.setText(R.string.mic_listening)
                btnMicA.setBackgroundResource(R.drawable.bg_mic_active)
                btnMicB.setText(R.string.mic_b)
                btnMicB.setBackgroundResource(R.drawable.bg_mic_b)
            }
            1 -> {
                btnMicB.setText(R.string.mic_listening)
                btnMicB.setBackgroundResource(R.drawable.bg_mic_active)
                btnMicA.setText(R.string.mic_a)
                btnMicA.setBackgroundResource(R.drawable.bg_mic_a)
            }
            else -> {
                btnMicA.setText(R.string.mic_a)
                btnMicA.setBackgroundResource(R.drawable.bg_mic_a)
                btnMicB.setText(R.string.mic_b)
                btnMicB.setBackgroundResource(R.drawable.bg_mic_b)
            }
        }
    }

    private fun swapLanguages() {
        val a = spinA.selectedItemPosition
        spinA.setSelection(spinB.selectedItemPosition, false)
        spinB.setSelection(a, false)
    }

    private fun copyDialog() {
        if (messages.isEmpty()) {
            Toast.makeText(this, R.string.translated_copied, Toast.LENGTH_SHORT).show()
            return
        }
        val sb = StringBuilder()
        for (m in messages) {
            val langAName = LANGS.first { it.first == langA }.second
            val langBName = LANGS.first { it.first == langB }.second
            val who = if (m.speaker == 0) langAName else langBName
            sb.append(who).append(": ").append(m.original).append("\n→ ").append(m.translated).append("\n\n")
        }
        val cm = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        cm.setPrimaryClip(ClipData.newPlainText("dialog", sb.toString().trim()))
        Toast.makeText(this, R.string.translated_copied, Toast.LENGTH_SHORT).show()
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERM_REQ) {
            if (grantResults.firstOrNull() == PackageManager.PERMISSION_GRANTED) {
                // Разрешение получено: если пользователь держал галочку — стартуем.
                val side = when {
                    chkA.isChecked -> 0
                    chkB.isChecked -> 1
                    else -> -1
                }
                if (side >= 0) startListening(side)
                else Toast.makeText(this, "Нажмите «Говорить»", Toast.LENGTH_SHORT).show()
            }
        }
    }

    /** Обработчик выбора языка в спиннерах. */
    private inner class SideSpinner(private val side: Int) : AdapterView.OnItemSelectedListener {
        override fun onItemSelected(parent: AdapterView<*>, view: View?, position: Int, id: Long) {
            val code = LANGS[position].first
            if (side == 0) langA = code else langB = code
            stopListening()
        }

        override fun onNothingSelected(parent: AdapterView<*>) {}
    }

    /** Адаптер истории диалога. */
    private inner class MsgAdapter : BaseAdapter() {
        override fun getCount(): Int = messages.size
        override fun getItem(position: Int): Any = messages[position]
        override fun getItemId(position: Int): Long = position.toLong()

        override fun getView(position: Int, convertView: View?, parent: ViewGroup): View {
            val view = convertView ?: LayoutInflater.from(this@MainActivity)
                .inflate(R.layout.list_item_msg, parent, false)
            val msg = messages[position]
            val tvWho = view.findViewById<TextView>(R.id.tvWho)
            val tvOriginal = view.findViewById<TextView>(R.id.tvOriginal)
            val tvTranslated = view.findViewById<TextView>(R.id.tvTranslated)
            val bubble = view.findViewById<View>(R.id.bubble)

            val params = bubble.layoutParams as FrameLayout.LayoutParams
            if (msg.speaker == 0) {
                params.gravity = Gravity.START
                bubble.setBackgroundResource(R.drawable.bg_bubble_a)
                tvWho.text = getString(R.string.speaker_a) + " (${langA})"
                tvWho.setTextColor(getColor(R.color.sideA_accent))
                tvTranslated.setTextColor(getColor(R.color.sideA_accent))
            } else {
                params.gravity = Gravity.END
                bubble.setBackgroundResource(R.drawable.bg_bubble_b)
                tvWho.text = getString(R.string.speaker_b) + " (${langB})"
                tvWho.setTextColor(getColor(R.color.sideB_accent))
                tvTranslated.setTextColor(getColor(R.color.sideB_accent))
            }
            bubble.layoutParams = params
            val targetCode = if (msg.speaker == 0) langB else langA
            val targetName = LANGS.firstOrNull { it.first == targetCode }?.second ?: targetCode
            tvOriginal.text = msg.original
            tvTranslated.text = "→ $targetName: ${msg.translated}"
            return view
        }
    }
}
