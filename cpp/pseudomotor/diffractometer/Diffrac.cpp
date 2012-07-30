#include <string>
#include <sstream>

#include "Diffrac.h"
#include <pool/PoolAPI.h>

using namespace std;

Controller::PropInfo Diffrac_class_prop[] = {
		{"OperationMode", "Operation mode: 'Symetric' or 'Fix incidence'", "DevString", ""},
		{"a", "Lattice 'a' parameter", "DevDouble", "2.84"},
		{"b", "Lattice 'b' parameter", "DevDouble", "2.84"},
		{"c", "Lattice 'c' parameter", "DevDouble", "2.84"},
		{"alpha", "Lattice alpha angle", "DevDouble", "90"},
		{"beta", "Lattice beta angle", "DevDouble", "90"},
		{"gamma", "Lattice gamma angle", "DevDouble", "90"},
		{"wavelength", "the source wavelength", "DevDouble", "2.84"},
		{"direction", "the X-rays beam direction", "DevString", "1 0 0"},
		{"reflections", "list of reflections. Each reflection is a list of 6 "
				        "numbers (space separated): th tth H K L lambda", "DevVarStringArray",""},
		{"DevName","The tango device name of the Diffractometer Device Server","DevString", "NONE"},
		{NULL} };

Diffrac::Diffrac(const char *inst,vector<Controller::Properties> &prop):
PseudoMotorController(inst),diffractometer(NULL)
{ }

Diffrac::~Diffrac ( ) 
{
	if (diffractometer)
		delete diffractometer;
}

void Diffrac::init(const char *inst,vector<Controller::Properties> &prop)
{
//	try 
//	{
		diffractometer = createDiffractometer();
		
		hkl::Geometry *g = diffractometer->geometry();
		
		// Adding the one and only sample (for now, at least)
		hkl::SampleList &s_list = diffractometer->samples();
		s_list.add(DFT_SAMPLE_NAME, hkl::SAMPLE_MONOCRYSTAL);
		s_list.set_current(DFT_SAMPLE_NAME);
		hkl::Sample *sample = s_list.current();
		hkl::Lattice & lattice = sample->lattice();
		
		double a,b,c,alpha,beta,gamma,wavelength;
		vector<string> *reflections = NULL;
		string *direction = NULL;
		
		for (unsigned long loop = 0;loop < prop.size();loop++)
		{
			string name = prop[loop].name;

			transform(name.begin(),name.end(),name.begin(),::tolower);
			
			if( name == "operationmode" )
			{
				diffractometer->modes().set_current(prop[loop].value.string_prop[0]);
			}
			else if( name == "a" )
			{
				a = prop[loop].value.double_prop[0];
			}
			else if( name == "b" )
			{
				b = prop[loop].value.double_prop[0];
			}
			else if( name == "c" )
			{	
				c = prop[loop].value.double_prop[0];
			}
			else if( name == "alpha" )
			{						
				alpha = prop[loop].value.double_prop[0];
			}
			else if( name == "beta" )
			{
				beta = prop[loop].value.double_prop[0];
			}
			else if( name == "gamma" )
			{
				gamma = prop[loop].value.double_prop[0];
			}
			else if( name == "wavelength" )
			{
				wavelength = prop[loop].value.double_prop[0];
			}
			else if( name == "reflections" )
			{
				reflections = &prop[loop].value.string_prop;
			}
			else if( name == "direction" )
			{
				direction = &prop[loop].value.string_prop[0];
			}
            else if( name == "devname")
			{
				DevName = prop[loop].value.string_prop[0];
                if(DevName != "NONE"){
					diffrac_device= Pool_ns::PoolUtil::instance()->get_device(inst_name, DevName);
					
					if(diffrac_device == NULL)
					{
						TangoSys_OMemStream o;
						o << "The PoolAPI did not provide a valid diffractometer device" << ends;
						Tango::Except::throw_exception((const char *)"DiffracCtrl_BadPoolAPI",o.str(),
													   (const char *)"DiffracCtrl");
					}
					
					try
					{
						diffrac_device->ping();
					}
					catch (Tango::DevFailed &e)
					{
						throw;
					}
				}
			}
		}
	
		// set the wavelength
		g->get_source().setWaveLength(wavelength);
	
		// set the direction
		if (direction)
		{
			double h,k,l;
			stringstream ss(*direction);
			string buf;
			ss >> buf;
			bool res = ToNumber(buf, h);
			ss >> buf;
			res &= ToNumber(buf, k);
			ss >> buf;
			res &= ToNumber(buf, l);
			if (res)
			{
				g->get_source().setDirection(hkl::svector(h,k,l));
			}
		}
	
		// set lattice parameters
		lattice.a().set_current(a);
		lattice.b().set_current(b);
		lattice.c().set_current(c);
		lattice.alpha().set_current(alpha * hkl::constant::math::degToRad);
		lattice.beta().set_current(beta * hkl::constant::math::degToRad);
		lattice.gamma().set_current(gamma * hkl::constant::math::degToRad);
		
		// add reflections
		if (reflections)
			setReflections(*reflections);
//	}
//	catch(hkl::HKLException &e)
//	{
//		throw_TangoException(e);
//	}
}

void Diffrac::throw_TangoException(hkl::HKLException &e)
{
	hkl::ErrorList &errors = e.errors;
	Tango::DevErrorList tg_errors(errors.size());
	tg_errors.length(errors.size());
	
	for(size_t idx = 0; idx < errors.size(); ++idx)
	{
		// HKL Panic errors should not be converted to Tango panic errors 
		// because they may force the pool to exit. 
		if (errors[idx].severity == hkl::ERR)
			tg_errors[idx].severity = Tango::ERR;
		else if (errors[idx].severity == hkl::WARN)
			tg_errors[idx].severity = Tango::WARN;
		else if (errors[idx].severity == hkl::PANIC)
			tg_errors[idx].severity = Tango::ERR;
		
		tg_errors[idx].desc = CORBA::string_dup(errors[idx].desc.c_str());
		tg_errors[idx].origin = CORBA::string_dup(errors[idx].origin.c_str());
		tg_errors[idx].reason = CORBA::string_dup(errors[idx].reason.c_str());
	}
	throw Tango::DevFailed(tg_errors);
}

string Diffrac::SendToCtrl(string &str)
{
	int i = 0;
	string buf;
	string cmd;
	stringstream ss(str);
	vector<string> params;
	while(ss >> buf)
	{
		if (i == 0)
			cmd = buf;
		else
			params.push_back(buf);
		i++;
	}
	
	bool question = cmd[0] == '?';
	if(question) cmd = cmd.substr(1);
	
	transform(cmd.begin(),cmd.end(),cmd.begin(),::tolower);
	
	const char *ret;

	if(cmd == "operationmode")
	{
		if (question)
			return getCurrentOperationMode();
		else{
            if(params[0] == "Bissector"){
				ret = setOperationMode(params[0]);
			} else {
				buf = params[0] + " " + params[1];
				ret = setOperationMode(buf);
			}
		}
	}
	else if(cmd == "currentsample")
	{
		if (question)
			return getCurrentSample();
		else
			ret = setCurrentSample(params[0]);
	}
	else if(cmd == "addsample")
	{
		ret = addSample(params[0]);
	}
	else if(cmd == "deletesample")
	{
		ret = addSample(params[0]);
	}
	else if( cmd == "a" )
	{
		if (question)
			return ToString(getCurrentSampleA());
		else
			ret = setCurrentSampleA(params[0]);
	}
	else if( cmd == "b" )
	{
		if (question)
			return ToString(getCurrentSampleB());
		else
			ret = setCurrentSampleB(params[0]);
	}
	else if( cmd == "c" )
	{
		if (question)
			return ToString(getCurrentSampleC());
		else
			ret = setCurrentSampleC(params[0]);
	}
	else if( cmd == "alpha" )
	{
		if (question)
			return ToString(getCurrentSampleAlpha());
		else
			ret = setCurrentSampleAlpha(params[0]);
	}
	else if( cmd == "beta" )
	{
		if (question)
			return ToString(getCurrentSampleBeta());
		else
			ret = setCurrentSampleBeta(params[0]);
	}
	else if( cmd == "gamma" )
	{
		if (question)
			return ToString(getCurrentSampleGamma());
		else
			ret = setCurrentSampleGamma(params[0]);
	}
	else if( cmd == "wavelength" )
	{
		if (question)
			return ToString(getWavelength());
		else
			ret = setWavelength(params[0]);
	}
	else if( cmd == "setor" )
	{
		ret = setReflection(params);
	}
	else if( cmd == "setlat" )
	{
		ret = setLattice(params);
	}
	else if( cmd == "direction" )
	{
		if (question)
			return getDirection();
		else
			ret = setDirection(params);
	}
	else if( cmd == "ub" )
	{
		if (question)
			return getUB();
		else
			return CMD_UNKNOWN;
	}
	else if( cmd == "geometry" )
	{
		if (question)
			return getDescription();
		else
			return CMD_UNKNOWN;
	}
	else if( cmd == "calca" )
	{
		return calcA(params);
	}
	else if( cmd == "calchkl" )
	{
		return calcHKL(params);
	}
    else if( cmd == "diffdev_h" )
	{
        if(diffrac_device != NULL)
		{
			if(question){
				Tango::DevDouble h_tmp;
				Tango::DeviceAttribute da = diffrac_device->read_attribute("h");
				da >> h_tmp;
				return ToString(h_tmp); 
			} else {
				ret = setDiffDevHKL(1, params);
			}
		} else {
			return "Not diffractometer device";
		}
	}
    else if( cmd == "diffdev_k" )
	{
        if(diffrac_device != NULL)
		{
			if(question){
				Tango::DevDouble k_tmp;
				Tango::DeviceAttribute da = diffrac_device->read_attribute("k");
				da >> k_tmp;
				return ToString(k_tmp); 
			} else {
				ret = setDiffDevHKL(2, params);
			}
		} else {
			return "Not diffractometer device";
		}
	}
    else if( cmd == "diffdev_l" )
	{
        if(diffrac_device != NULL)
		{
			if(question){
				Tango::DevDouble l_tmp;
				Tango::DeviceAttribute da = diffrac_device->read_attribute("l");
				da >> l_tmp;
				return ToString(l_tmp); 
			} else {
				ret = setDiffDevHKL(3, params);
			}
		} else {
			return "Not Diffractometer Device";
		}
	}
    else if (cmd == "diffdev_sethkl")
	{
		if(diffrac_device != NULL)
		{
			ret = setDiffDevHKL(0, params);   
		} else {
			return "Not Diffractometer Device";
		}
	}
    else if( cmd == "diffdev_a" )
	{
        if(diffrac_device != NULL)
		{
			if(question){
				Tango::DevDouble a_tmp;
				Tango::DeviceAttribute da = diffrac_device->read_attribute("a");
				da >> a_tmp;
				return ToString(a_tmp); 
			} 
		} else {
			return "Not Diffractometer Device";
		}
	}
    else if( cmd == "diffdev_b" )
	{
        if(diffrac_device != NULL)
		{
			if(question){
				Tango::DevDouble b_tmp;
				Tango::DeviceAttribute da = diffrac_device->read_attribute("b");
				da >> b_tmp;
				return ToString(b_tmp); 
			} 
		} else {
			return "Not Diffractometer Device";
		}
	}
    else if( cmd == "diffdev_c" )
	{
        if(diffrac_device != NULL)
		{
			if(question){
				Tango::DevDouble c_tmp;
				Tango::DeviceAttribute da = diffrac_device->read_attribute("c");
				da >> c_tmp;
				return ToString(c_tmp); 
			} 
		} else {
			return "Not Diffractometer Device";
		}
	}
    else if( cmd == "diffdev_alpha" )
	{
        if(diffrac_device != NULL)
		{
			if(question){
				Tango::DevDouble alpha_tmp;
				Tango::DeviceAttribute da = diffrac_device->read_attribute("alpha");
				da >> alpha_tmp;
				return ToString(alpha_tmp); 
			} 
		} else {
			return "Not Diffractometer Device";
		}
	}
    else if( cmd == "diffdev_beta" )
	{
        if(diffrac_device != NULL)
		{
			if(question){
				Tango::DevDouble beta_tmp;
				Tango::DeviceAttribute da = diffrac_device->read_attribute("beta");
				da >> beta_tmp;
				return ToString(beta_tmp); 
			} 
		} else {
			return "Not Diffractometer Device";
		}
	}
    else if( cmd == "diffdev_gamma" )
	{
        if(diffrac_device != NULL)
		{
			if(question){
				Tango::DevDouble gamma_tmp;
				Tango::DeviceAttribute da = diffrac_device->read_attribute("gamma");
				da >> gamma_tmp;
				return ToString(gamma_tmp); 
			} 
		} else {
			return "Not Diffractometer Device";
		}
	}
    else if( cmd == "diffdev_wavelength" )
	{
        if(diffrac_device != NULL)
		{
			if(question){
				Tango::DevDouble wl_tmp;
				Tango::DeviceAttribute da = diffrac_device->read_attribute("waveLength");
				da >> wl_tmp;
				return ToString(wl_tmp); 
			} 
		} else {
			return "Not Diffractometer Device";
		}
	}
	else
	{
		return CMD_UNKNOWN;
	}
	return ret;
}

string Diffrac::getDescription()
{
	stringstream ss;
	ss << *diffractometer->geometry() << "\n" << getCurrentLatticeRef();
	return ss.str();
}

string Diffrac::getUB()
{
	stringstream ss;
	ss << getCurrentSampleRef().get_UB();
	return ss.str();
}

string Diffrac::getDirection()
{
	hkl::Geometry *g = diffractometer->geometry();
	const hkl::svector &dir = g->get_source().get_direction();
	stringstream ss;
	ss << dir.x() << " " << dir.y() << " " << dir.z();
	return ss.str();
}

const char *Diffrac::setDirection(vector<string> &params)
{
	double h, k, l;
	if(!ToNumber(params[0], h) ||
	   !ToNumber(params[1], k) ||
	   !ToNumber(params[2], l))
		return UNABLE_TO_PARSE_CMD_LINE;
	
	hkl::Geometry *g = diffractometer->geometry();
	g->get_source().setDirection(hkl::svector(h,k,l));
	return CMD_OK;
}

void Diffrac::setLattice(double a, double b, double c, double alpha, 
                         double beta, double gamma)
{
	hkl::Lattice &lattice = getCurrentLatticeRef();

	lattice.a().set_current(a);
	lattice.b().set_current(b);
	lattice.c().set_current(c);
	lattice.alpha().set_current(alpha * hkl::constant::math::degToRad);
	lattice.beta().set_current(beta * hkl::constant::math::degToRad);
	lattice.gamma().set_current(gamma * hkl::constant::math::degToRad);	
}

const char *Diffrac::setLattice(vector<string> &params)
{
	if (params.size() < 6)
		return SET_LAT_WRONG_PARAMS;
	
	double a, b, c, alpha, beta, gamma;
	if(!ToNumber(params[0], a) ||
	   !ToNumber(params[1], b) ||
	   !ToNumber(params[2], c) ||
	   !ToNumber(params[3], alpha) ||
	   !ToNumber(params[4], beta) ||
	   !ToNumber(params[5], gamma))
		return UNABLE_TO_PARSE_CMD_LINE;

	hkl::Lattice &lattice = getCurrentLatticeRef();

	lattice.a().set_current(a);
	lattice.b().set_current(b);
	lattice.c().set_current(c);
	lattice.alpha().set_current(alpha * hkl::constant::math::degToRad);
	lattice.beta().set_current(beta * hkl::constant::math::degToRad);
	lattice.gamma().set_current(gamma * hkl::constant::math::degToRad);
	
	return CMD_OK;
}

double Diffrac::getWavelength()
{
	return diffractometer->geometry()->get_source().get_waveLength().get_value();
}

const char *Diffrac::setWavelength(const string &value)
{
	double wavelength;
	if(!ToNumber(value, wavelength))
		return UNABLE_TO_PARSE_CMD_LINE;
	diffractometer->geometry()->get_source().setWaveLength(wavelength);
	return CMD_OK;
}

double Diffrac::getCurrentSampleGamma()
{
	hkl::Lattice & lattice = getCurrentLatticeRef();
	return lattice.gamma().get_current().get_value() * hkl::constant::math::radToDeg;
}

const char *Diffrac::setCurrentSampleGamma(const string &value)
{
	hkl::Lattice & lattice = getCurrentLatticeRef();
	
	double gamma;
	if(!ToNumber(value, gamma))
		return UNABLE_TO_PARSE_CMD_LINE;
	lattice.gamma().set_current(gamma * hkl::constant::math::degToRad);
	return CMD_OK;
}

double Diffrac::getCurrentSampleBeta()
{
	hkl::Lattice & lattice = getCurrentLatticeRef();
	return lattice.beta().get_current().get_value() * hkl::constant::math::radToDeg;
}

const char *Diffrac::setCurrentSampleBeta(const string &value)
{
	hkl::Lattice & lattice = getCurrentLatticeRef();
	
	double beta;
	if(!ToNumber(value, beta))
		return UNABLE_TO_PARSE_CMD_LINE;
	lattice.beta().set_current(beta * hkl::constant::math::degToRad);
	return CMD_OK;
}

double Diffrac::getCurrentSampleAlpha()
{
	hkl::Lattice & lattice = getCurrentLatticeRef();
	return lattice.alpha().get_current().get_value() * hkl::constant::math::radToDeg;
}

const char *Diffrac::setCurrentSampleAlpha(const string &value)
{
	hkl::Lattice & lattice = getCurrentLatticeRef();
	
	double alpha;
	if(!ToNumber(value, alpha))
		return UNABLE_TO_PARSE_CMD_LINE;
	lattice.alpha().set_current(alpha * hkl::constant::math::degToRad);
	return CMD_OK;
}

double Diffrac::getCurrentSampleC()
{
	hkl::Lattice & lattice = getCurrentLatticeRef();
	return lattice.c().get_current().get_value();
}

const char *Diffrac::setCurrentSampleC(const string &value)
{
	hkl::Lattice & lattice = getCurrentLatticeRef();
	
	double c;
	if(!ToNumber(value, c))
		return UNABLE_TO_PARSE_CMD_LINE;
	lattice.c().set_current(c);
	return CMD_OK;
}

double Diffrac::getCurrentSampleB()
{
	hkl::Lattice & lattice = getCurrentLatticeRef();
	return lattice.b().get_current().get_value();
}

const char *Diffrac::setCurrentSampleB(const string &value)
{
	hkl::Lattice & lattice = getCurrentLatticeRef();
	
	double b;
	if(!ToNumber(value, b))
		return UNABLE_TO_PARSE_CMD_LINE;
	lattice.b().set_current(b);
	return CMD_OK;
}

double Diffrac::getCurrentSampleA()
{
	hkl::Lattice & lattice = getCurrentLatticeRef();
	return lattice.a().get_current().get_value();
}

const char *Diffrac::setCurrentSampleA(const string &value)
{
	hkl::Lattice & lattice = getCurrentLatticeRef();
	
	double a;
	if(!ToNumber(value, a))
		return UNABLE_TO_PARSE_CMD_LINE;
	lattice.a().set_current(a);
	return CMD_OK;
}

const char *Diffrac::deleteSample(const string& sample_name)
{
	hkl::SampleList &s_list = diffractometer->samples();
	hkl::Sample *sample = s_list[sample_name];
	hkl::SampleList::iterator it = find(s_list.begin(), s_list.end(), sample);
	s_list.erase(it);
	return CMD_OK;
}

const char *Diffrac::addSample(const string& sample_name)
{
	hkl::SampleList &s_list = diffractometer->samples();
	s_list.add(sample_name, hkl::SAMPLE_MONOCRYSTAL);
	return CMD_OK;
}

string Diffrac::ToString(double v)
{
	std::stringstream strm;
	strm << v;
	return strm.str();
}

bool Diffrac::ToNumber(const string &str, double &v)
{
	istringstream iss(str);
	if(!(iss >> v))
		return false;
	return true;
}

bool Diffrac::ToNumber(const string &str, int &v)
{
	istringstream iss(str);
	if(!(iss >> v))
		return false;
	return true;
}

hkl::Lattice &Diffrac::getCurrentLatticeRef()
{
	return getCurrentSampleRef().lattice();
}

hkl::Sample &Diffrac::getCurrentSampleRef()
{
	hkl::Sample *s = diffractometer->samples().current();
	if (!s)
	{
		Tango::Except::throw_exception("Diffrac_NoCurrentSample",\
										"Diffrac has no current sample.", 
										"Diffrac::getCurrentSampleRef()");\
	}
	return *s;
}

hkl::Mode &Diffrac::getCurrentOperationModeRef()
{
	hkl::Mode *m = diffractometer->modes().current();
	if (!m)
	{
		Tango::Except::throw_exception("Diffrac_NoCurrentOperationMode",\
										"Diffrac has no current operation mode.", 
										"Diffrac::getCurrentOperationModeRef()");\
	}
	return *m;
}

string Diffrac::getCurrentSample()
{
	return getCurrentSampleRef().get_name();
}

const char *Diffrac::setCurrentSample(const string &sample_name)
{
	hkl::SampleList &s_list = diffractometer->samples();
	s_list.set_current(sample_name);
	return CMD_OK;
}

string Diffrac::getCurrentOperationMode()
{
	return getCurrentOperationModeRef().get_name();
}

const char *Diffrac::setOperationMode(const string &mode)
{
	diffractometer->modes().set_current(mode);
	return CMD_OK;
}

void Diffrac::tokenize(const string& str, vector<string>& tokens, const string& delimiters)
{
    // Skip delimiters at beginning.
    string::size_type lastPos = str.find_first_not_of(delimiters, 0);
    // Find first "non-delimiter".
    string::size_type pos     = str.find_first_of(delimiters, lastPos);

    while (string::npos != pos || string::npos != lastPos)
    {
        // Found a token, add it to the vector.
        tokens.push_back(str.substr(lastPos, pos - lastPos));
        // Skip delimiters.  Note the "not_of"
        lastPos = str.find_first_not_of(delimiters, pos);
        // Find next "non-delimiter"
        pos = str.find_first_of(delimiters, lastPos);
    }
}

const char *Diffrac::setDiffDevHKL(int index, vector<string> &params)
{ 

    double h,k,l;
	double a;

    if( (index > 0) ){
		if(!ToNumber(params[0], a))
			return UNABLE_TO_PARSE_CMD_LINE;
	} else if( (index == 0) ){
		if(!ToNumber(params[0], h) ||
		   !ToNumber(params[1], k) ||
		   !ToNumber(params[2], l))
			return UNABLE_TO_PARSE_CMD_LINE;
	}
 
	if(index == 1){
		Tango::DeviceAttribute *da = new Tango::DeviceAttribute("h", (double)a);
		diffrac_device->write_attribute(*da );
	} else if (index == 2){
		Tango::DeviceAttribute *da = new Tango::DeviceAttribute("k", (double)a); 
		diffrac_device->write_attribute(*da );
	} else if (index == 3){
		Tango::DeviceAttribute *da = new Tango::DeviceAttribute("l", (double)a); 
		diffrac_device->write_attribute(*da );
	} else if (index == 0){
		Tango::DeviceData dd;
		Tango::DeviceData dout;
		Tango::DevVarDoubleArray *in = new Tango::DevVarDoubleArray();
		in->length(3);
		(*in)[0] = h;
		(*in)[1] = k;
		(*in)[2] = l;
		dd << in;
		try
		{
			diffrac_device->command_inout("SetHKL",dd);
		}
		catch(Tango::DevFailed &e)
		{
			cout << "Error in command_inout SetHKL" << endl;
		}

	}
	
	return CMD_OK;
}

