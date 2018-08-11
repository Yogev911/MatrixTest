import json



def create_res_obj(data, success=True):
    '''
    create return obj with array of data.
    :param data: dict of 'data_obj'
    :param success: json format for response
    :return:
    '''
    return json.dumps({
        "success": success,
        "data": data
    })


def data_obj(author, content, docname, path):
    '''
    create node of data object
    :param author: string
    :param content: string
    :param docname: string
    :param path: string
    :return: data_obj
    '''
    return {
        "docname": docname,
        "author": author,
        "path": path,
        "content": content
    }


