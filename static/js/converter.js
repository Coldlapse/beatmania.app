function bms2iidx(){
    let bmssudden = document.getElementById("beatoraja_sudden").value;
    let iidxsudden = document.getElementById("iidx_sudden").value;
    let lift = document.getElementById("lift").value;
    let result;
    result = Math.floor(bmssudden * ( (1000 - lift) / 1000));
    document.getElementById("iidx_sudden").value = result;
}

function iidx2bms(){
	let bmssudden = document.getElementById("beatoraja_sudden").value;
    let iidxsudden = document.getElementById("iidx_sudden").value;
    let lift = document.getElementById("lift").value;
    let result;
    result = Math.floor(iidxsudden * ( 1000 / (1000 - lift)));
    document.getElementById("beatoraja_sudden").value = result;
}

function liftconvert(){
    let bmssudden = document.getElementById("beatoraja_sudden").value;
    let iidxsudden = document.getElementById("iidx_sudden").value;
    let lift = document.getElementById("lift").value;
    let changelift = document.getElementById("converted_lift").value;
    let iidxresult;
    let bmsresult;
    if ((changelift >= 0) == false) {
        alert("변환할 리프트 값을 입력하지 않았습니다!");
        return 0
    }
    if (bmssudden >= 0) {
        bmsresult = Math.floor((Math.floor(bmssudden * ( (1000 - lift) / 1000)) - (changelift - lift)) * ( 1000 / (1000 - changelift)));
        document.getElementById("converted_beatoraja").value = bmsresult;
    }
    if (iidxsudden >= 0) {
        iidxresult = iidxsudden - (changelift - lift);
        document.getElementById("converted_iidx").value = iidxresult;
    }
}