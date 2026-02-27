#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gradio 接口：调用 marlin 解码接口并流式播放音频
"""
import io
import requests
import gradio as gr
import numpy as np


def decode_and_play_audio(marlin_url: str, bin_file_path: str):
    """
    调用 marlin 解码接口，解码 bin 文件并返回音频数据
    
    Args:
        marlin_url: marlin 服务的基础 URL，例如 "http://localhost:8080"
        bin_file_path: bin 文件的路径
    
    Returns:
        tuple: (sample_rate, audio_data) 用于 gradio 播放
    """
    if not marlin_url or not bin_file_path:
        return None, "请提供 marlin URL 和 bin 文件路径"
    
    # 构建解码接口 URL
    decode_url = f"{marlin_url}/marlin/v1/audio/decode"
    
    try:
        # 调用解码接口（流式返回）
        response = requests.get(
            decode_url,
            params={"file": bin_file_path},
            stream=True,
            timeout=30
        )
        response.raise_for_status()
        
        # 读取流式数据
        audio_bytes = b""
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                audio_bytes += chunk
        
        if len(audio_bytes) == 0:
            return None, "解码失败：未收到音频数据"
        
        # 解析 WAV 文件
        # WAV 文件格式：44 字节头 + PCM 数据
        if len(audio_bytes) < 44:
            return None, f"音频数据太短：{len(audio_bytes)} 字节"
        
        # 从 WAV 头中读取采样率和声道信息
        sample_rate = int.from_bytes(audio_bytes[24:28], byteorder='little')
        num_channels = int.from_bytes(audio_bytes[22:24], byteorder='little')
        bits_per_sample = int.from_bytes(audio_bytes[34:36], byteorder='little')
        
        # 提取 PCM 数据（跳过 44 字节 WAV 头）
        pcm_data = audio_bytes[44:]
        
        # 转换为 numpy 数组
        if bits_per_sample == 16:
            # 16-bit PCM
            audio_array = np.frombuffer(pcm_data, dtype=np.int16)
        elif bits_per_sample == 32:
            # 32-bit PCM
            audio_array = np.frombuffer(pcm_data, dtype=np.int32)
        else:
            return None, f"不支持的位深：{bits_per_sample} bits"
        
        # 归一化到 [-1, 1] 范围
        if bits_per_sample == 16:
            audio_array = audio_array.astype(np.float32) / 32768.0
        elif bits_per_sample == 32:
            audio_array = audio_array.astype(np.float32) / 2147483648.0
        
        # 处理多声道（如果是立体声，需要 reshape）
        if num_channels == 2:
            audio_array = audio_array.reshape(-1, 2)
        
        return sample_rate, audio_array
        
    except requests.exceptions.RequestException as e:
        return None, f"请求失败：{str(e)}"
    except Exception as e:
        return None, f"处理失败：{str(e)}"


def create_gradio_interface():
    """创建 Gradio 界面"""
    
    def play_audio(marlin_url, bin_file_path):
        """播放音频的回调函数"""
        if not marlin_url or not bin_file_path:
            return None, "请填写 marlin URL 和 bin 文件路径"
        
        sample_rate, audio_data = decode_and_play_audio(marlin_url, bin_file_path)
        
        if sample_rate is None:
            # 返回错误信息
            return None, audio_data
        
        return sample_rate, audio_data
    
    # 创建 Gradio 界面
    with gr.Blocks(title="Opus 音频解码播放器") as demo:
        gr.Markdown("# Opus 音频解码播放器")
        gr.Markdown("调用 marlin 解码接口，解码 bin 文件并播放音频")
        
        with gr.Row():
            with gr.Column():
                marlin_url_input = gr.Textbox(
                    label="Marlin 服务 URL",
                    placeholder="http://localhost:18088",
                    value="http://localhost:18088"
                )
                bin_file_input = gr.Textbox(
                    label="Bin 文件路径",
                    placeholder="/path/to/audio.bin",
                    value=""
                )
                play_button = gr.Button("解码并播放", variant="primary")
            
            with gr.Column():
                audio_output = gr.Audio(
                    label="解码后的音频",
                    type="numpy",
                    autoplay=True
                )
                status_output = gr.Textbox(
                    label="状态信息",
                    lines=3,
                    interactive=False
                )
        
        # 绑定事件
        play_button.click(
            fn=play_audio,
            inputs=[marlin_url_input, bin_file_input],
            outputs=[audio_output, status_output]
        )
        
        # 示例
        gr.Markdown("### 使用示例")
        gr.Markdown("""
        - Marlin URL: `http://localhost:8080` 或你的 marlin 服务地址
        - Bin 文件路径: 例如 `/root/xjliu/yunxiao/marlin/output/input.bin`
        """)
    
    return demo


if __name__ == "__main__":
    demo = create_gradio_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

