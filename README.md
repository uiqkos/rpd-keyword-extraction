## Получение ключевых слов из РПД 
## Пример

```python
MARKERS = (
    'Планируемые результаты обучения',
    'Наименование раздела дисциплины',
    'Наименование раздела дисциплины (модуля)',
    'Содержание',

    # ГИА
    'Наименование оценочного средства',
)

df = pd.read_csv(DATA_PATH / 'raw' / 'data.csv')
df = df.head(1)

pipeline = Pipeline(
    stages=[
        Download(save_path=DATA_PATH / 'documents'),
        ConvertToPdf(),
        ExtractTables(save_path=DATA_PATH / 'tables'),
        ExtractKeywords(markers=MARKERS, flatten_results=True),
        EmbeddingGrouper(
            vectorizer=FrequencyVectorizer(
                tokenizer=Tokenizer(
                    vectors=RuWikiRuscorporaCBOW_300_10_2021
                        .load(MODELS_PATH / 'embeddings')
                )
            ),
            model=DBSCAN(
                eps=0.08,
                min_samples=2,
                metric='cosine'
            ),
            keyword_group_factory=KeywordGroupFactory(
                algorithm='most_common_bigram'
            )
        )
    ],
    generator=False,
    verbose=True
)

res = pipeline.apply(*df[['FILE_ID', 'FILE_NAME', 'URL']].values, orient='rows')

print(res)
```
```
Download: 100%|█████████████████████████████████████████████████████| 1/1 [00:00<00:00, 1004.38it/s]
ConvertToPdf: 100%|███████████████████████████████████████████████████████████| 1/1 [00:00<?, ?it/s]
ExtractTables: 100%|██████████████████████████████████████████████████| 1/1 [00:12<00:00, 12.23s/it]
ExtractKeywords: 100%|███████████████████████████████████████████████| 1/1 [00:00<00:00, 496.13it/s]
EmbeddingGrouper: 100%|███████████████████████████████████████████████████████| 1/1 [00:00<?, ?it/s]
Embeddings: 100%|████████████████████████████████████████████████████| 2/2 [00:00<00:00, 998.76it/s]
[KeywordGroup(center='Базовые положения', keywords={'Базовые положения начертательной геометрии'}), KeywordGroup(center='Инженерная графика', keywords={'Инженерная графика'})]
```
