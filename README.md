# Incremental Search-Based Allocation of Autonomous Robots for Goods Delivery
Autonomous robots can solve different issues of delivery services, by guaranteeing less traffic congestion, less pollution, and lower operational costs. Designing such type of delivery system based on autonomous robots requires the collaboration of different stakeholders, having different concerns: the store utilising the delivery service that is interested in costs and customer satisfaction, the municipality where the service is operated that is interested in the safety of the service, and the robotic company providing the service that is interested in all previous concerns. The Panasonic company is designing this type of service in Fujisawa, Japan, and using a simulator for assessing different configurations providing different levels of performance. Since manually designing the configurations is time consuming for engineers, in this paper, we propose a search-based approach (All) that is able to explore the space of service configurations and find the optimal ones that show the trade-off existing among the different concerns, so that stakeholders can make an informed decision. Since assessing one configuration requires to simulate the service multiple times over different types of customer requests, the approach suffers from scalability issues. Therefore, we propose two improvements of the approach that reduce the number of required simulations (IncrSim), and the duration of the simulation (IncrTime). Experiments on different settings show that IncrSim and IncrTime can find results as good as those of All in less time, and better than versions of All executed for the same budget. 

## Installation 

Create a virtual environment and activate it.
```
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies. 
```
pip install -r requirements.txt
```

### Simulator 
For IP protection, the simulator is not available. Still, you can use *mock mode* (see below) if you don't have the simulator.

### Executing a single search 

``` 
python delivery-search.py   --generations $generations 
                            --population $population 
                            --offspring-population $offspring 
                            --min-requests $min_requests 
                            --max-requests $max_requests 
                            --speed $speed --robots $robots 
                            --capacity $capacity 
                            --duration $duration 
                            --run-tag $run_tag 
                            --seed $sim_seed 
                            --simulations $simulations 
                            --problem $problem 
                            --approach $approach 
                            --results-dir $folder
                            
```

You can use the flag `--mock` to obtain random data locally if you do not have the simulator.

## People
* Paolo Arcaini http://group-mmm.org/~arcaini/
* Ezequiel Castellano https://jp.linkedin.com/in/ezequiel-castellano-7076962b
* Fuyuki Ishikawa http://research.nii.ac.jp/~f-ishikawa/en/
* Hirokazu Kawamoto
* Kaoru Sawai
* Eiichi Muramoto
