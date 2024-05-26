This repository contains **ViSpeR**, a large-scale dataset and models for Visual Speech Recognition for Arabic, Chinese, French and Spanish.

## Dataset Summary:

Given the scarcity of publicly available VSR data for non-English languages, we collected VSR data for the most four spoken languages at scale.


Comparison of VSR datasets. Our proposed ViSpeR dataset is larger in size compared to other datasets that cover non-English languages for the VSR task. For our dataset, the numbers in parenthesis denote the number of clips. We also give the clip coverage under TedX and Wild subsets of our ViSpeR dataset.

| Dataset         | French (fr)     | Spanish (es)    | Arabic (ar)     | Chinese (zh)    |
|-----------------|-----------------|-----------------|-----------------|-----------------|
| **MuAVIC**      | 176             | 178             | 16              | --              |
| **VoxCeleb2**   | 124             | 42              | --              | --              |
| **AVSpeech**    | 122             | 270             | --              | --              |
| **ViSpeR (TedX)** | 192 (160k)    | 207 (151k)      | 49 (48k)        | 129 (143k)      |
| **ViSpeR (Wild)** | 799 (548k)    | 851 (531k)      | 1152 (1.01M)    | 658 (593k)      |
| **ViSpeR (full)** | 991 (709k)    | 1058 (683k)     | 1200 (1.06M)    | 787 (736k)      |


## Downloading the data:

First, use the langauge.json to download the videos and put them in seperate folders. The raw data should be structured as follows:
```bash
Data/
├── Chinese/
│ ├── video_id.mp4
│ └── ...
├── Arabic/
│ ├── video_id.mp4
│ └── ...
├── French/
│ ├── video_id.mp4
│ └── ...
├── Spanish/
│ ├── video_id.mp4
│ └── ...

```

## Setup:

1- Setup the environement:
 ```bash
conda create --name visper python=3.10
conda activate visper
pip install -r requirements.txt
```

2- Install ffmpeg:
 ```bash
conda install "ffmpeg<5" -c conda-forge
```

## Processing the data:

You need the download the meta data from [HF](https://huggingface.co/datasets/tiiuae/visper), this includes ```train.tar.gz``` and ```test.tar,gz```. Then, use the provided metadata to process the raw data for creating the ViSpeR dataset. You can use the ```crop_videos.py``` to process the data, note that all clips are cropped and transformed

| Languages | Split | Link |
|----------|---------------|----------------|
| en,fr, es, ar, cz   | train          | [train](https://huggingface.co/datasets/tiiuae/visper/train.tar.gz)          |
| en,fr, es, ar, cz   | test          | [test](https://huggingface.co/tiiuae/visper/test.tar.gz)          |



```bash
python crop_videos.py --video_dir [path_to_data_language] --save_path [save_path_language] --json [language_metadata.json] --use_ffmpeg True
```

```bash
ViSpeR/
├── Chinese/
│ ├── video_id/
│ │  │── 00001.mp4
│ │  │── 00001.json
│ └── ...
├── Arabic/
│ ├── video_id/
│ │  │── 00001.mp4
│ │  │── 00001.json
│ └── ...
├── French/
│ ├── video_id/
│ │  │── 00001.mp4
│ │  │── 00001.json
│ └── ...
├── Spanish/
│ ├── video_id/
│ │  │── 00001.mp4
│ │  │── 00001.json
│ └── ...

```

The ```video_id/xxxx.json``` has the 'label' of the corresponding video ```video_id/xxxx.mp4```.

## Multilingual ViSPer
The processed multilingual VSR video-text pairs are utilized to train a multilingual encoder-decoder model in a fully-supervised manner. The supported languages are: English, Arabic, French, Spanish and Chinese. For English, we leverage the combined 1759H from LRS3 and VoxCeleb-en. While the encoder size is 12 layers, the decoder size is 6 layers. The hidden size, MLP and number of heads are set to 768, 3072 and 12, respectively. The unigram tokenizers are learned on all languages and have a vocabulary size of 21k. Results are presented here:


| Language | VSR (WER/CER) | AVSR (WER/CER) |
|----------|---------------|----------------|
| French   | 29.8          | 5.7            |
| Spanish  | 39.4          | 4.4            |
| Arabic   | 47.8          | 8.4            |
| Chinese  | 51.3 (CER)    | 15.4 (CER)     |
| English  | 49.1          | 8.1            |

Model weights to be found at [HF](https://huggingface.co/tiiuae/visper)

| Languages | Task | Size |Checkpoint |
|----------|---------------|----------------|----------------|
| en,fr, es, ar, cz   | AVSR          | Base |[visper_avsr_base.pth](https://huggingface.co/tiiuae/visper/blob/main/visper_avsr_base.pth)          |
| en,fr, es, ar, cz   | VSR          |  Base |[visper_vsr_base.pth](https://huggingface.co/tiiuae/visper/blob/main/visper_vsr_base.pth)          |


## Intended Use

This dataset can be used to train models for visual speech recognition. It's particularly useful for research and development purposes in the field of audio-visual content processing. The data can be used to assess the performance of current and future models.

## Limitations and Biases
Due to the data collection process focusing on YouTube, biases inherent to the platform may be present in the dataset. Also, while measures are taken to ensure diversity in content, the dataset might still be skewed towards certain types of content due to the filtering process.


## Citation
```bash

@inproceedings{djilali2023lip2vec,
  title={Lip2Vec: Efficient and Robust Visual Speech Recognition via Latent-to-Latent Visual to Audio Representation Mapping},
  author={Djilali, Yasser Abdelaziz Dahou and Narayan, Sanath and Boussaid, Haithem and Almazrouei, Ebtessam and Debbah, Merouane},
  booktitle={Proceedings of the IEEE/CVF International Conference on Computer Vision},
  pages={13790--13801},
  year={2023}
}

@inproceedings{djilali2024vsr,
  title={Do VSR Models Generalize Beyond LRS3?},
  author={Djilali, Yasser Abdelaziz Dahou and Narayan, Sanath and LeBihan, Eustache and Boussaid, Haithem and Almazrouei, Ebtesam and Debbah, Merouane},
  booktitle={Proceedings of the IEEE/CVF Winter Conference on Applications of Computer Vision},
  pages={6635--6644},
  year={2024}
}
```
