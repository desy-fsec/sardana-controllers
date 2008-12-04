#ifndef DIFFRAC2C_H_
#define DIFFRAC2C_H_

#include <vector>
#include <pool/PseudoMotCtrl.h>
#include <Diffrac.h>
#include <hkl/diffractometerfactory.h>

#define SET_REFLEC_WRONG_PARAMS		"Usage: setor <index> <tth> <th> <h> <k> <l>"

extern "C"
{
	Controller *_create_Diffrac2C(const char *,std::vector<Controller::Properties> &);
}

class Diffrac2C : public Diffrac
{
protected:
	
	hkl::twoC::vertical::Geometry &getGeometry();
	
	virtual hkl::Diffractometer* createDiffractometer();
	virtual const char *setReflection(vector<string> &);
	virtual void setReflections(vector<string> &);
	
	virtual string calcA(vector<string> &);
	virtual string calcHKL(vector<string> &);

public:
	Diffrac2C(const char *,std::vector<Controller::Properties> &);
	virtual ~Diffrac2C();
	
	virtual double CalcPhysical(int32_t, std::vector<double> &);
	virtual double CalcPseudo(int32_t, std::vector<double> &);   
	/**
	 * Overwritten implementation for efficiency reasons
	 * 
	 * @param	pseudo_pos		[in]	list of pseudo motor positions
	 * @param	physical_pos	[out]	list of physical motor positions
	 * 
	 * @warnning It is crucial that this method is called with physical_pos 
	 *           vector containning the correct number of elements.
	 */ 
	virtual void CalcAllPhysical(std::vector<double> &, std::vector<double> &);
};

#endif /*DIFFRAC2C_H_*/
