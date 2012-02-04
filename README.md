

REST Stockmarket
=================

REST Stockmarket sample REST API for a  stockmarket-like application, 
It demonstrates how this can be implemented in Python, using MongoDB + Bottle, and different techniques to implement transactional behaviours with this stack.   

A Stockmarket 
-------------

* GET /portofolio/X . Retrieves the portofolio for user "X" as a JSON object : 

		{ user : X , content :
		 	{ market_name : 
		 		{ stock_name : count, 
				  stock_name : count
				 }
		} 
		
* POST /stockexchange/distribute. Distribute a set of stocks to a user. Accepts a JSON object with similar structure

		{ 
			"user" : X, content : ... 
		}
	
* POST /stockexchange/trade. Exchange a set of stocks between two users. Accept a JSON object

		{ 
		"portofolio_1" : { user : U1, content : ... }, 
		"portofolio_2" : { user : U2, content : ... }
		}

	The content described in portofolio_1 is transfered from U1 to U2, and the content from portofolio_2 is transfered from U2 to U1  
	
Several implementation are featured: 
------------------

* naive_stockmarket.py :  A Naive implementation, with no validation or transactional guarantees

* lessnative_stockmarket.py  : Features MongoDB atomic operations. No validation of transfers .. 

* lock_stockmarket.py : Performs validation of transfers. Ensure consistency by locking. 

* transac_stockmarket.py : Performs validation and use two-phase commits to ensure proper transactional behaviour 
  
 