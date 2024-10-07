import numpy
import numpy.typing
import numba



NUMBA_PARAMS = dict(cache=True)



# numba.bool_(numba.uint32, numba.uint32, numba.uint8)
@numba.njit(**NUMBA_PARAMS)
def dotProduct(a: int, b: int, size: int) -> int:
    mul = a & b
    dot = 0
    for _ in range(size):
        dot ^= (mul & 0b1)
        mul >>= 1
    return dot



# numba.bool_[:](numba.bool_[:], numba.uint8, numba.uint32, numba.uint32, numba.uint32)
@numba.njit(**NUMBA_PARAMS)
def convolve(data: numpy.typing.NDArray[numpy.bool_],
             constraint_length: int,
             polynomial: int,
             initial_state: int,
             final_state: int
             )-> numpy.typing.NDArray[numpy.bool_]:

    data_size = len(data)
    input_mask = 0b1 << (constraint_length - 1)
    emission_size = data_size + constraint_length - 1

    convoluted = numpy.empty(emission_size, dtype=numpy.bool_)
    state = initial_state

    for data_index in range(data_size):
        data_bit = data[data_index]
        state >>= 1
        state |= (data_bit << (constraint_length - 1))

        convoluted_bit = dotProduct(state, polynomial, constraint_length)
        convoluted[data_index] = convoluted_bit

    tail = final_state
    
    for tail_index in range(constraint_length - 1):
        state >>= 1
        state |= tail & input_mask
        tail <<= 1

        convoluted_bit = dotProduct(state, polynomial, constraint_length)
        convoluted[data_size + tail_index] = convoluted_bit
    
    return convoluted



@numba.njit(**NUMBA_PARAMS)
def deconvolve(convoluted: numpy.typing.NDArray[numpy.bool_],
               constraint_length: int,
               polynomial: int,
               initial_state: int
               ) -> numpy.typing.NDArray[numpy.bool_]:

    data_size = len(convoluted)

    data = numpy.empty(data_size, dtype=numpy.bool_)
    state = initial_state

    for data_index in range(data_size):
        convoluted_bit = convoluted[data_index]
        state >>= 1
        window = state | (convoluted_bit << (constraint_length - 1))
        
        data_bit = dotProduct(window, polynomial, constraint_length)
        
        data[data_index] = data_bit
        state |= (data_bit << (constraint_length - 1))
    
    return data



# locals=dict(expected_emission_1=numba.bool_, expected_emission_2=numba.bool_)
@numba.njit(**NUMBA_PARAMS)
def softViterbiDecode(observed_emissions: numpy.typing.NDArray[numpy.float32],
                    constraint_length: int,
                    initial_state: int,
                    final_state: int|None,
                    polynomials: numpy.typing.NDArray[numpy.uint]|None =None,
                    emission_table: numpy.typing.NDArray[numpy.bool_]|None =None,
                    ) -> numpy.typing.NDArray[numpy.bool_]:
    
    if polynomials is not None:
        _polynomials = polynomials
    if emission_table is not None:
        _emission_table = emission_table

    n_states = 2 ** (constraint_length - 1)
    n_emissions = observed_emissions.shape[0]
    emission_size = observed_emissions.shape[1]
    data_size = emission_size - constraint_length + 1
    state_mask = n_states - 1

    from_states = numpy.empty((emission_size, n_states), dtype=numpy.uint32)
    path_metrics = numpy.empty((emission_size + 1, n_states))
    path_metrics[0, :] = numpy.inf
    path_metrics[0, initial_state] = 0

    for data_index in range(emission_size):
        for state in range(n_states):
            previous_window_1 = (state << 1)
            previous_window_2 = previous_window_1 | 0b1
            previous_state_1 = previous_window_1 & state_mask
            previous_state_2 = previous_window_2 & state_mask
            branch_metric_1 = 0
            branch_metric_2 = 0

            for emission_index in range(n_emissions):
                if emission_table is not None:
                    expected_emission_1 = _emission_table[emission_index, previous_window_1]
                    expected_emission_2 = _emission_table[emission_index, previous_window_2]
                elif polynomials is not None:
                    expected_emission_1 = dotProduct(previous_window_1, _polynomials[emission_index], constraint_length) * 2 - 1
                    expected_emission_2 = dotProduct(previous_window_2, _polynomials[emission_index], constraint_length) * 2 - 1

                #branch_metric_1 += abs(expected_emission_1 - observed_emissions[emission_index, data_index])
                #branch_metric_2 += abs(expected_emission_2 - observed_emissions[emission_index, data_index])
                branch_metric_1 += (expected_emission_1 - observed_emissions[emission_index, data_index]) ** 2
                branch_metric_2 += (expected_emission_2 - observed_emissions[emission_index, data_index]) ** 2
            
            branch_metric_1 = branch_metric_1 ** 0.5
            branch_metric_2 = branch_metric_2 ** 0.5

            path_metric_1 = path_metrics[data_index, previous_state_1] + branch_metric_1
            path_metric_2 = path_metrics[data_index, previous_state_2] + branch_metric_2

            if path_metric_1 < path_metric_2:
                path_metrics[data_index + 1, state] = path_metric_1
                from_states[data_index, state] = previous_state_1
            else:
                path_metrics[data_index + 1, state] = path_metric_2
                from_states[data_index, state] = previous_state_2
    
    data = numpy.empty(data_size, dtype=numpy.bool_)
    if final_state is not None:
        state = final_state
    else:
        state = path_metrics[emission_size, :].argmin()

    for data_index in range(emission_size - 1, -1, -1):
        if data_index < data_size:
            data_bit = state >> (constraint_length - 2)
            data[data_index] = data_bit
        state = from_states[data_index, state]

    return data



@numba.njit(**NUMBA_PARAMS)
def generateEmissionTable(constraint_length: int,
                          polynomials: list[int]
                          ) -> numpy.typing.NDArray[numpy.int8]:
    
    n_emissions = len(polynomials)
    n_windows = 2 ** constraint_length

    emission_table = numpy.empty((n_emissions, n_windows), dtype=numpy.int8)

    for emission_index, poly in enumerate(polynomials):
        for window in range(n_windows):
            emission_table[emission_index, window] = dotProduct(window, poly, constraint_length) * 2 - 1

    return emission_table