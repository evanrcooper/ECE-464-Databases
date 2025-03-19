import requests
import os
import sys
import pathlib as pl
import helper_scripts.db_utils as db
import helper_scripts.db_init as db_init
import datetime as dt

# database_path: str = '/evanr/ece464.sqlite3'
# database_init_path: str = '/app/db_init.sql'

database_directory_path: pl.Path = pl.Path('/evanr')
database_path: pl.Path = database_directory_path / 'ece464.sqlite3'
database_init_path: str = './WebApp/db_init.sql'

def main() -> None:
    if not os.path.exists(database_path):
        if not db_init.db_init(database_path, database_init_path):
            raise Exception('Unable to initialize database\n')
    db_manager: db.DBManager = db.DBManager(database_path, database_directory_path)
    
    create_user_success, log = db_manager.create_user('admin', '0000C0DE')
    if not create_user_success:
        print(log)
    
    log_in_success, log = db_manager.log_in('admin', '0000C0DE')
    if not log_in_success:
        print(log)
        return
    else:
        token = log 
        print(f'{token = }')
    
    time = str(dt.datetime.now())
    print(f'creating article, timestamp = {time}')
    create_article_success, log = db_manager.create_article(token, 'A neural network (NN) is a computational model inspired by the structure and function of the human brain, designed to recognize patterns, process data, and make decisions. Neural networks are a fundamental component of machine learning and artificial intelligence, used in tasks such as image recognition, natural language processing, and autonomous systems. At their core, neural networks consist of layers of interconnected nodes, known as neurons, that transform input data through weighted connections and activation functions. These layers are typically divided into three main categories: the input layer, hidden layers, and the output layer. The input layer receives raw data, such as pixels in an image or numerical values in a dataset, and passes it to subsequent layers. Hidden layers perform feature extraction and pattern recognition, enabling the network to learn complex relationships within the data. The output layer produces the final result, such as a classification label or a predicted value. Each neuron in a neural network receives input from multiple sources, applies a mathematical transformation using learned weights, and passes the result through an activation function. The activation function introduces non-linearity, allowing the network to learn intricate patterns beyond simple linear relationships. Common activation functions include the sigmoid function, which outputs values between 0 and 1; the ReLU (Rectified Linear Unit) function, which outputs zero for negative values and retains positive values; and the softmax function, often used in classification tasks to generate probability distributions. Neural networks learn through a process called training, which involves adjusting the weights of connections between neurons to minimize the error in predictions. This is achieved using an optimization algorithm known as backpropagation combined with gradient descent. During training, the network processes input data, compares its predictions to known correct outputs (labels), and computes an error using a loss function. The loss function quantifies the difference between the predicted and actual values. Backpropagation calculates the gradient of the loss function with respect to each weight in the network, propagating the error backward from the output layer to the earlier layers. The gradient descent algorithm then updates the weights in the direction that reduces the error, gradually improving the network’s accuracy. This iterative process continues until the network achieves satisfactory performance. Neural networks can be categorized into various types based on their architecture and application. Feedforward neural networks, the simplest type, process data in a single direction from input to output. Convolutional neural networks (CNNs) are specialized for image processing, using convolutional layers to detect spatial features such as edges and textures. Recurrent neural networks (RNNs) are designed for sequential data, such as time series and natural language, incorporating memory elements that retain information from previous inputs. More advanced architectures, such as transformers, have revolutionized language processing by efficiently handling long-range dependencies in text. Despite their power, neural networks have challenges, including the need for large datasets, computational intensity, and the risk of overfitting, where a model memorizes training data instead of generalizing. Techniques such as regularization, dropout, and batch normalization help mitigate these issues. As research progresses, neural networks continue to evolve, driving advancements in AI and enabling applications across numerous fields, from healthcare and finance to autonomous vehicles and robotics.', 'article title', dt.date.today(), 'evan rosenfeld')
    if not create_article_success:
        print(log)
        return
    else:
        article_id = log
        print(f'{article_id = }')
    
    get_article_success, log = db_manager.get_article_text(article_id)
    if not get_article_success:
        print(log)
        return
    else:
        article_text = log
        print(f'\n\n\n{article_text = }\n\n\n')
        
    get_article_summary_success, log = db_manager.get_article_summary(token, article_id)
    if not get_article_summary_success:
        print(log)
        return
    else:
        article_summary = log
        print(f'\n\n\n{article_summary = }\n\n\n')
        
    log_out_success, log = db_manager.log_out(token=token)
    if not log_out_success:
        print(log)
        return
    else:
        print('logged out successfully')
        
    print('test successful')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
    except KeyboardInterrupt as k:
        sys.stderr.write(f'KeyboardInterrupt: {str(k)}')
        sys.stderr.write('User Interrupt\n')