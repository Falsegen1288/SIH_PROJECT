import React, { useEffect } from 'react';
import UploadPage from '../components/UploadPage';
import './Home.css';

export default function Home() {
  useEffect(() => {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate');
        }
      });
    }, { threshold: 0.25 });

    document
      .querySelectorAll('.model-heading, .model-text')
      .forEach(el => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return (
    <div className="snap-container">
      <section className="snap-page">
        <UploadPage />
      </section>

      <section className="snap-page model-page">
        <div className="model-heading">What does our model do?</div>
        <div className="model-text">
          First our model preprocesses the dataset using normalization,
          time-indexing and missing-data handling. Then our{' '}
          <strong>LSTM + CNN</strong> model predicts future prices, and finally
          applies <strong>Bollinger Bands</strong> to identify government
          intervention dates.
        </div>
      </section>

      <section className="snap-page model-page">
        <div className="model-heading"> Why was ARIMA rejected and deep learning adopted?
</div>
        <div className="model-text">
          ARIMA was tested but failed to capture the complexities in the price time series — it showed high error and limited ability to model non-linearities. In contrast, the hybrid CNN-LSTM model significantly outperformed ARIMA by learning both short-term patterns (via Conv1D) and long-term dependencies (via LSTM), making it more suitable for real-world forecasting.
        </div>
      </section>
    <section className="snap-page model-page">
        <div className="model-heading"> What kind of neural network is used in this model?
</div>
        <div className="model-text">
         The model uses a hybrid CNN-LSTM architecture:

Conv1D layers act as temporal filters, capturing short-term local trends in the time series.

Bidirectional LSTM layers learn long-term temporal dependencies in both forward and backward directions.
This combination enhances performance in predicting complex time-dependent patterns.
        </div>
      </section>
      <section className="snap-page model-page">
        <div className="model-heading">Why Bollinger Bands?</div>
        <div className="model-text">
          Bollinger Bands are a popular technical analysis tool used in financial
          markets to measure market volatility and identify potential buy or sell
          signals based on price movement. Incorporating them on the prediction
          gives us our final answer: the intervention dates.
        </div>
      </section>
        <section className="snap-page model-page">
        <div className="model-heading">How can I use this model for another product or market?
</div>
        <div className="model-text">
         To adapt the model:

Change the PLACE variable to the column name of your desired product (e.g., "Tomato").

Load your dataset in the same format (Date, Product, etc.).

Rerun the notebook — preprocessing, training, and evaluation will be done automatically.
Make sure the dataset has enough historical data and a similar structure for best results.
        </div>
      </section>
     <section className="snap-page model-page">
  <div className="model-heading">Contact us</div>
  <div className="model-text contact-links">
    <a href="mailto:strangemridul@gmail.com" target="_blank" rel="noopener noreferrer">
      Email
    </a>
    <a href="https://github.com/Falsegen1288/SIH_PROJECT" target="_blank" rel="noopener noreferrer">
      GitHub
    </a>
    <a href="https://www.linkedin.com/in/mridul-chouhan-iitg/" target="_blank" rel="noopener noreferrer">
      LinkedIn
    </a>
     <a target="_blank" rel="noopener noreferrer">
      +91-7067539702
    </a>
  </div>
</section>


    </div>
  );
}
