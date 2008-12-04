#ifndef SLIT_H_
#define SLIT_H_

#include <pool/PseudoMotCtrl.h>
#include <vector>

extern "C"
{
	Controller *_create_Slit(const char *,vector<Controller::Properties> &);
}

/**
 * A Pseudo motor controller for a Slit 
 */
class Slit:public PseudoMotorController
{
public:
	Slit(const char *,vector<Controller::Properties> &);
	virtual ~Slit();
	
	virtual double CalcPhysical(int32_t, vector<double> &);
	virtual double CalcPseudo(int32_t, vector<double> &);
};

#endif /*SLIT_H_*/
