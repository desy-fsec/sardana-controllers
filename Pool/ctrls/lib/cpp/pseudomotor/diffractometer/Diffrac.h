#ifndef DIFFRAC_H_
#define DIFFRAC_H_

#include <vector>
#include <pool/PseudoMotCtrl.h>
#include <hkl/diffractometerfactory.h>

#define DFT_SAMPLE_NAME           "DefaultSample"
#define CMD_OK                    "true"
#define CMD_ERR                   "error"
#define CMD_UNKNOWN               "Unknown command"
#define UNABLE_TO_PARSE_CMD_LINE  "Unable to parse command line. One or more parameters have wrong type"
#define SET_LAT_WRONG_PARAMS      "Usage: setlat <a> <b> <c> <alpha> <beta> <gamma>"
class Diffrac : public PseudoMotorController
{
protected:
	
	hkl::DiffractometerFactory df_factory;	
	hkl::Diffractometer *diffractometer;
	
	virtual void init(const char *,vector<Controller::Properties> &);
	
	string getDescription();
	string getCurrentOperationMode();
	string getUB();
	string getDirection();
	double getWavelength();
	string getCurrentSample();
	double getCurrentSampleA();
	double getCurrentSampleB();
	double getCurrentSampleC();
	double getCurrentSampleAlpha();
	double getCurrentSampleBeta();
	double getCurrentSampleGamma();

	const char *setDirection(vector<string> &);
	const char *setLattice(vector<string> &);
	const char *setWavelength(const string &);	
	const char *setOperationMode(const string &);
	const char *setCurrentSample(const string &);
	const char *setCurrentSampleA(const string &);
	const char *setCurrentSampleB(const string &);
	const char *setCurrentSampleC(const string &);
	const char *setCurrentSampleAlpha(const string &);
	const char *setCurrentSampleBeta(const string &);
	const char *setCurrentSampleGamma(const string &);
	
	const char *deleteSample(const string&);
	const char *addSample(const string&);
	
	bool ToNumber(const string &, double &);
	bool ToNumber(const string &, int &);
	string ToString(double);
	hkl::Lattice &getCurrentLatticeRef();
	hkl::Sample &getCurrentSampleRef();
	hkl::Mode &getCurrentOperationModeRef();
	void tokenize(const string& , vector<string>& , const string& delimiters = " ");

    const char *setDiffDevHKL(int index, vector<string> &);
	
	void throw_TangoException(hkl::HKLException &);
	
	virtual hkl::Diffractometer* createDiffractometer() { return NULL; }
	
	virtual void setLattice(double, double, double, double, double, double);
	virtual const char *setReflection(vector<string> &) = 0;
	virtual void setReflections(vector<string> &) = 0;
	
	virtual string calcA(vector<string> &) = 0;
	virtual string calcHKL(vector<string> &) = 0;

    string DevName;
    Tango::DeviceProxy      *diffrac_device;
	
public:
	Diffrac(const char *,std::vector<Controller::Properties> &);
	virtual ~Diffrac();
	
	//virtual double CalcPhysical(long,std::vector<double> &);
	//virtual double CalcPseudo(long,std::vector<double> &);

	virtual std::string SendToCtrl(std::string &);
};

#endif /*DIFFRAC2C_H_*/
