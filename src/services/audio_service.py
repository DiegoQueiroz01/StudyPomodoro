import asyncio
import discord
from pathlib import Path

AUDIO_DIR = Path(__file__).parent.parent / "assets" / "audio"


class AudioService:
    """Gerencia a conexão com o canal de voz e a reprodução de áudios/músicas."""

    @staticmethod
    async def get_or_connect_voice(voice_channel: discord.VoiceChannel) -> discord.VoiceClient:
        """Conecta ou recupera o cliente de voz do bot no canal especificado."""
        guild = voice_channel.guild
        voice_client = guild.voice_client

        if voice_client is None:
            voice_client = await voice_channel.connect()
        elif voice_client.channel.id != voice_channel.id:
            await voice_client.move_to(voice_channel)

        return voice_client

    @staticmethod
    def stop_audio(voice_client: discord.VoiceClient):
        """Para qualquer áudio em reprodução no momento."""
        if voice_client and voice_client.is_playing():
            voice_client.stop()

    @staticmethod
    async def play_sound(voice_client: discord.VoiceClient, filename: str):
        """Reproduz um efeito sonoro pontual."""
        audio_path = AUDIO_DIR / filename
        if not audio_path.exists():
            print(f"[Aviso Áudio] Arquivo não encontrado: {audio_path}")
            return

        AudioService.stop_audio(voice_client)
        source = discord.FFmpegPCMAudio(str(audio_path))
        voice_client.play(source)

    @staticmethod
    async def play_sound_then_music(
        voice_client: discord.VoiceClient, sound_filename: str, music_filename: str
    ):
        """Toca o sinal sonoro primeiro e, ao finalizar, inicia a música correspondente em loop."""
        sound_path = AUDIO_DIR / sound_filename
        music_path = AUDIO_DIR / music_filename

        if not sound_path.exists():
            print(f"[Aviso Áudio] Arquivo não encontrado: {sound_path}")
            return

        AudioService.stop_audio(voice_client)

        loop = asyncio.get_running_loop()

        async def delayed_start_music():
            """Aguarde o buffer do voice_client liberar totalmente antes de iniciar a música."""
            await asyncio.sleep(0.5)
            
            if music_path.exists() and voice_client and voice_client.is_connected():
                # Argumentos de entrada do FFmpeg para garantir loop infinito estável
                ffmpeg_options = {
                    'before_options': '-stream_loop -1',
                    'options': '-vn'
                }
                
                music_source = discord.FFmpegPCMAudio(
                    str(music_path),
                    before_options=ffmpeg_options['before_options'],
                    options=ffmpeg_options['options']
                )
                voice_client.play(music_source)

        def play_music_after_sound(error):
            if error:
                print(f"[Erro Áudio] Falha na reprodução do alarme: {error}")
                return

            # Agenda a corrotina assíncrona na thread principal do bot
            asyncio.run_coroutine_threadsafe(delayed_start_music(), loop)

        # Toca o sinal sonoro inicial
        sound_source = discord.FFmpegPCMAudio(str(sound_path))
        voice_client.play(sound_source, after=play_music_after_sound)

    @staticmethod
    async def disconnect_voice(guild: discord.Guild):
        """Desconecta o bot do canal de voz ao encerrar a sessão."""
        if guild.voice_client:
            await guild.voice_client.disconnect()